
# 模組二：空間／物品預約借用

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from db import getDB
from routes.auth import get_current_user, require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# =====================================
# 1. 預約首頁與每週借用查詢
# =====================================

@router.get("/")
async def index(
    request: Request,
    room_id: int | None = None,
    week_date: date | None = None,
    conn=Depends(getDB)
):

    # 取得所有教室與可借用物品
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT id, code, name
            FROM rooms
            ORDER BY code
        """)
        rooms = await cur.fetchall()

        await cur.execute("""
            SELECT id, name, total_quantity
            FROM items
            ORDER BY id
        """)
        items = await cur.fetchall()

    # 找出選擇的教室
    selected_room = next(
        (room for room in rooms if room["id"] == room_id),
        None
    )

    # 計算選擇日期所在的星期
    chosen_date = week_date or date.today()

    monday = chosen_date - timedelta(
        days=chosen_date.weekday()
    )

    weekdays = [
        "星期一", "星期二", "星期三",
        "星期四", "星期五", "星期六", "星期日"
    ]

    week_days = []

    for i in range(7):
        current_day = monday + timedelta(days=i)

        week_days.append({
            "date": current_day.isoformat(),
            "weekday": weekdays[i]
        })

    # 查詢該教室本週的預約紀錄
    bookings = []

    if selected_room:
        sunday = monday + timedelta(days=6)

        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT
                    booking_date,
                    start_time,
                    end_time,
                    status
                FROM bookings
                WHERE room_id = %s
                  AND booking_date BETWEEN %s AND %s
                  AND status IN ('pending', 'approved')
                ORDER BY booking_date, start_time
            """, (room_id, monday, sunday))

            bookings = await cur.fetchall()

    # 將資料傳給 HTML
    return templates.TemplateResponse(
        request,
        "booking/index.html",
        {
            "user": get_current_user(request),
            "rooms": rooms,
            "items": items,
            "selected_room": selected_room,
            "week_date": chosen_date.isoformat(),
            "week_days": week_days,
            "bookings": bookings
        }
    )


# =====================================
# 2. 新增預約申請
# =====================================

@router.post("/create")
async def create_booking(
    request: Request,
    conn=Depends(getDB)
):

    # 只有登入者才能預約
    user = require_login(request)

    form = await request.form()

    try:
        room_id = int(form["room_id"])

        booking_date = date.fromisoformat(
            str(form["booking_date"])
        )

        start_time = datetime.strptime(
            str(form["start_time"]), "%H:%M"
        ).time()

        end_time = datetime.strptime(
            str(form["end_time"]), "%H:%M"
        ).time()

        # 取得選擇的借用物品
        item_ids = [
            int(value)
            for value in form.getlist("item_ids")
        ]

        if len(item_ids) != len(set(item_ids)):
            raise ValueError("重複物品")

        quantities = {}

        for item_id in item_ids:
            quantities[item_id] = int(
                form[f"quantity_{item_id}"]
            )

    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="預約資料格式不正確"
        )

    # 檢查預約日期
    if booking_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="不能預約過去的日期"
        )

    # 檢查開始與結束時間
    if start_time >= end_time:
        raise HTTPException(
            status_code=400,
            detail="結束時間必須晚於開始時間"
        )

    # 檢查物品數量
    if any(q <= 0 for q in quantities.values()):
        raise HTTPException(
            status_code=400,
            detail="借用數量必須大於 0"
        )

    # 使用資料庫交易
    async with conn.transaction():
        async with conn.cursor() as cur:

            # 確認教室存在
            await cur.execute("""
                SELECT id
                FROM rooms
                WHERE id = %s
                FOR UPDATE
            """, (room_id,))

            if await cur.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="找不到教室"
                )

            # 檢查教室時間是否衝突
            await cur.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM bookings
                    WHERE room_id = %s
                      AND booking_date = %s
                      AND start_time < %s
                      AND end_time > %s
                      AND status IN ('pending', 'approved')
                ) AS has_conflict
            """, (
                room_id,
                booking_date,
                end_time,
                start_time
            ))

            result = await cur.fetchone()

            if result["has_conflict"]:
                raise HTTPException(
                    status_code=409,
                    detail="這間教室在此時段已有預約"
                )

            # 檢查物品借用數量
            if quantities:
                await cur.execute("""
                    SELECT id, name, total_quantity
                    FROM items
                    WHERE id = ANY(%s)
                    ORDER BY id
                    FOR UPDATE
                """, (sorted(quantities),))

                selected_items = await cur.fetchall()

                if len(selected_items) != len(quantities):
                    raise HTTPException(
                        status_code=400,
                        detail="選擇的物品不存在"
                    )

                for item in selected_items:

                    await cur.execute("""
                        SELECT COALESCE(
                            SUM(bi.quantity), 0
                        ) AS reserved
                        FROM booking_items bi
                        JOIN bookings b
                          ON bi.booking_id = b.id
                        WHERE bi.item_id = %s
                          AND b.booking_date = %s
                          AND b.start_time < %s
                          AND b.end_time > %s
                          AND b.status IN ('pending', 'approved')
                    """, (
                        item["id"],
                        booking_date,
                        end_time,
                        start_time
                    ))

                    stock = await cur.fetchone()

                    available = (
                        item["total_quantity"]
                        - stock["reserved"]
                    )

                    if quantities[item["id"]] > available:
                        raise HTTPException(
                            status_code=409,
                            detail=f"{item['name']} 數量不足"
                        )

            # 建立待審核預約
            await cur.execute("""
                INSERT INTO bookings (
                    user_id,
                    room_id,
                    booking_date,
                    start_time,
                    end_time,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, 'pending')
                RETURNING id
            """, (
                user["id"],
                room_id,
                booking_date,
                start_time,
                end_time
            ))

            new_booking = await cur.fetchone()
            booking_id = new_booking["id"]

            # 儲存借用物品
            for item_id, quantity in quantities.items():
                await cur.execute("""
                    INSERT INTO booking_items (
                        booking_id,
                        item_id,
                        quantity
                    )
                    VALUES (%s, %s, %s)
                """, (
                    booking_id,
                    item_id,
                    quantity
                ))

    return RedirectResponse(
        url=(
            f"/booking/?room_id={room_id}"
            f"&week_date={booking_date.isoformat()}"
        ),
        status_code=303
    )


# =====================================
# 3. 管理員查看預約紀錄
# =====================================

@router.get("/admin")
async def admin_bookings(
    request: Request,
    conn=Depends(getDB)
):

    # 只有管理員可以查看
    user = require_login(
        request,
        roles=("admin",)
    )

    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT
                b.id,
                u.username,
                r.code AS room_code,
                r.name AS room_name,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                b.review_comment,
                b.checked_out_at,
                b.returned_at
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY b.created_at DESC, b.id DESC
        """)

        bookings = await cur.fetchall()

    return templates.TemplateResponse(
        request,
        "booking/admin.html",
        {
            "user": user,
            "bookings": bookings
        }
    )


# =====================================
# 4. 管理員核准或退件
# =====================================

@router.post("/admin/review")
async def review_booking(
    request: Request,
    conn=Depends(getDB)
):

    require_login(
        request,
        roles=("admin",)
    )

    form = await request.form()

    try:
        booking_id = int(form["booking_id"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="預約編號不正確"
        )

    action = str(form.get("action", ""))

    review_comment = str(
        form.get("review_comment", "")
    ).strip()

    if action not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail="審核動作不正確"
        )

    if len(review_comment) > 1000:
        raise HTTPException(
            status_code=400,
            detail="審核意見不能超過1000字"
        )

    async with conn.transaction():
        async with conn.cursor() as cur:

            # 鎖定預約，避免重複審核
            await cur.execute("""
                SELECT id, status
                FROM bookings
                WHERE id = %s
                FOR UPDATE
            """, (booking_id,))

            booking = await cur.fetchone()

            if booking is None:
                raise HTTPException(
                    status_code=404,
                    detail="找不到預約"
                )

            if booking["status"] != "pending":
                raise HTTPException(
                    status_code=409,
                    detail="這筆預約已經審核"
                )

            # 更新審核狀態及意見
            await cur.execute("""
                UPDATE bookings
                SET status = %s,
                    review_comment = %s
                WHERE id = %s
            """, (
                action,
                review_comment,
                booking_id
            ))

    return RedirectResponse(
        url="/booking/admin",
        status_code=303
    )


# =====================================
# 5. 管理員確認借出
# =====================================

@router.post("/admin/checkout")
async def checkout_booking(
    request: Request,
    conn=Depends(getDB)
):

    require_login(
        request,
        roles=("admin",)
    )

    form = await request.form()

    try:
        booking_id = int(form["booking_id"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="預約編號不正確"
        )

    async with conn.transaction():
        async with conn.cursor() as cur:

            await cur.execute("""
                SELECT status, checked_out_at, returned_at
                FROM bookings
                WHERE id = %s
                FOR UPDATE
            """, (booking_id,))

            booking = await cur.fetchone()

            if booking is None:
                raise HTTPException(
                    status_code=404,
                    detail="找不到預約"
                )

            if booking["status"] != "approved":
                raise HTTPException(
                    status_code=409,
                    detail="預約尚未核准，不能借出"
                )

            if booking["checked_out_at"] is not None:
                raise HTTPException(
                    status_code=409,
                    detail="這筆預約已經借出"
                )

            # 記錄借出時間
            await cur.execute("""
                UPDATE bookings
                SET checked_out_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (booking_id,))

            # 同時記錄借用物品
            await cur.execute("""
                UPDATE booking_items
                SET checked_out_at = CURRENT_TIMESTAMP
                WHERE booking_id = %s
                  AND checked_out_at IS NULL
            """, (booking_id,))

    return RedirectResponse(
        url="/booking/admin",
        status_code=303
    )


# =====================================
# 6. 管理員確認歸還
# =====================================

@router.post("/admin/return")
async def return_booking(
    request: Request,
    conn=Depends(getDB)
):

    require_login(
        request,
        roles=("admin",)
    )

    form = await request.form()

    try:
        booking_id = int(form["booking_id"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="預約編號不正確"
        )

    async with conn.transaction():
        async with conn.cursor() as cur:

            await cur.execute("""
                SELECT status, checked_out_at, returned_at
                FROM bookings
                WHERE id = %s
                FOR UPDATE
            """, (booking_id,))

            booking = await cur.fetchone()

            if booking is None:
                raise HTTPException(
                    status_code=404,
                    detail="找不到預約"
                )

            if booking["status"] != "approved":
                raise HTTPException(
                    status_code=409,
                    detail="只有核准的預約可以歸還"
                )

            if booking["checked_out_at"] is None:
                raise HTTPException(
                    status_code=409,
                    detail="尚未借出，不能歸還"
                )

            if booking["returned_at"] is not None:
                raise HTTPException(
                    status_code=409,
                    detail="這筆預約已經歸還"
                )

            # 記錄歸還時間
            await cur.execute("""
                UPDATE bookings
                SET returned_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (booking_id,))

            # 同時記錄所有借用物品
            await cur.execute("""
                UPDATE booking_items
                SET returned_at = CURRENT_TIMESTAMP
                WHERE booking_id = %s
                  AND checked_out_at IS NOT NULL
                  AND returned_at IS NULL
            """, (booking_id,))

    return RedirectResponse(
        url="/booking/admin",
        status_code=303
    )


# =====================================
# 7. 我的借用紀錄（這次新增）
# =====================================

@router.get("/history")
async def booking_history(
    request: Request,
    conn=Depends(getDB)
):

    # 必須登入才能查看自己的紀錄
    user = require_login(request)

    # 只查詢目前登入者的預約
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT
                b.id,
                r.code AS room_code,
                r.name AS room_name,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                b.review_comment,
                b.checked_out_at,
                b.returned_at,

                COALESCE((
                    SELECT STRING_AGG(
                        i.name || ' × ' || bi.quantity::TEXT,
                        '、'
                        ORDER BY i.name
                    )
                    FROM booking_items bi
                    JOIN items i ON bi.item_id = i.id
                    WHERE bi.booking_id = b.id
                ), '') AS items_summary

            FROM bookings b
            JOIN rooms r ON b.room_id = r.id

            WHERE b.user_id = %s

            ORDER BY b.created_at DESC, b.id DESC
        """, (user["id"],))

        bookings = await cur.fetchall()

    # 將自己的紀錄傳給 HTML
    return templates.TemplateResponse(
        request,
        "booking/history.html",
        {
            "user": user,
            "bookings": bookings
        }
    )
