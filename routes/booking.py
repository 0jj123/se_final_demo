
# 模組二：空間／物品預約借用

from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from db import getDB
from routes.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(
    request: Request,
    room_id: int | None = None,
    week_date: date | None = None,
    conn=Depends(getDB)
):

    # 取得所有教室
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT id, code, name
            FROM rooms
            ORDER BY code
        """)
        rooms = await cur.fetchall()

    # 取得所有可借用物品
    async with conn.cursor() as cur:
        await cur.execute("""
            SELECT id, name, total_quantity
            FROM items
            ORDER BY id
        """)
        items = await cur.fetchall()

    # 找出使用者選擇的教室
    selected_room = next(
        (room for room in rooms if room["id"] == room_id),
        None
    )

    # 計算選擇日期所在的星期
    chosen_date = week_date or date.today()

    monday = chosen_date - timedelta(
        days=chosen_date.weekday()
    )

    # 產生星期一到星期日的日期
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

    # 查詢這間教室本週的預約紀錄
    bookings = []

    if selected_room:
        sunday = monday + timedelta(days=6)

        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT booking_date, start_time, end_time, status
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
