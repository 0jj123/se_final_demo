# 模組二：空間/物品預約借用
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from db import getDB
from routes.auth import get_current_user, require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(request: Request):
	return templates.TemplateResponse(request, "booking/index.html", {"user": get_current_user(request)})

# TODO: 在這裡加你的功能
