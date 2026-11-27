
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

    # 取得所有教室及物品
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

    # 計算星期一到星期日
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

    # 查詢選定教室本週的預約
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

    # 必須登入才能預約
    user = require_login(request)

    form = await request.form()

    # 檢查輸入資料
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

    # 不可預約過去的日期
    if booking_date < date.today():
        raise HTTPException(
            status_code=400,
            detail="不能預約過去的日期"
        )

    # 結束時間必須晚於開始時間
    if start_time >= end_time:
        raise HTTPException(
            status_code=400,
            detail="結束時間必須晚於開始時間"
        )

    # 借用數量必須大於零
    if any(q <= 0 for q in quantities.values()):
        raise HTTPException(
            status_code=400,
            detail="借用數量必須大於 0"
        )

    # 同一次交易中檢查並建立預約
    async with conn.transaction():
        async with conn.cursor() as cur:

            # 確認教室存在並鎖定
            await cur.execute("""
                SELECT id
                FROM rooms
                WHERE id = %s
                FOR UPDATE
            """, (room_id,))

            if await cur.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="找不到這間教室"
                )

            # 檢查預約時間衝突
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

            # 檢查借用物品數量
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
                            detail=f"{item['name']} 可借數量不足"
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

            # 儲存選擇的物品
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
# 3. 管理員查看預約申請
# =====================================

@router.get("/admin")
async def admin_bookings(
    request: Request,
    conn=Depends(getDB)
):

    # 只有管理員可以進入
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
                b.review_comment
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

    # 只有管理員可以審核
    require_login(
        request,
        roles=("admin",)
    )

    # 取得審核表單
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

    # 只能核准或退件
    if action not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail="審核動作不正確"
        )

    # 限制審核意見長度
    if len(review_comment) > 1000:
        raise HTTPException(
            status_code=400,
            detail="審核意見不能超過1000字"
        )

    # 更新預約狀態
    async with conn.transaction():
        async with conn.cursor() as cur:

            # 取得並鎖定這筆預約
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
                    detail="找不到這筆預約"
                )

            # 只有待審核的預約能審核
            if booking["status"] != "pending":
                raise HTTPException(
                    status_code=409,
                    detail="這筆預約已經完成審核"
                )

            # 儲存核准或退件結果
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

    # 審核完成後返回管理員頁面
    return RedirectResponse(
        url="/booking/admin",
        status_code=303
    )
