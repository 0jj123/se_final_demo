# main.py（共用，只負責掛載 router，盡量不要改）
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from db import lifespan
from routes.auth import router as authRoute, get_current_user
from routes.space import router as spaceRoute
from routes.booking import router as bookingRoute
from routes.schedule import router as scheduleRoute

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "dev"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(authRoute)                          # /login /logout /register
app.include_router(spaceRoute, prefix="/space")        # 模組一：空間查詢
app.include_router(bookingRoute, prefix="/booking")    # 模組二：預約借用
app.include_router(scheduleRoute, prefix="/schedule")  # 模組三：排課


@app.get("/")
async def home(request: Request):
	return templates.TemplateResponse(request, "index.html", {"user": get_current_user(request)})
