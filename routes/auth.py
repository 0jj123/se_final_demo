# 共用：帳號註冊、審核、登入、登出（負責人：___）
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ===== 共用工具：其他模組 import 這兩個來檢查登入 / 權限 =====
# session 格式：request.session["user"] = {"id": 1, "username": "xxx", "role": "teacher"}

def get_current_user(request: Request):
	"""回傳目前登入者 dict，沒登入回傳 None"""
	return request.session.get("user")


def require_login(request: Request, roles: tuple = ()):
	"""用法：user = require_login(request, roles=("admin",))"""
	user = get_current_user(request)
	if not user:
		raise HTTPException(status_code=401, detail="請先登入")
	if roles and user["role"] not in roles:
		raise HTTPException(status_code=403, detail="權限不足")
	return user


# ===== 路由（TODO：負責人實作） =====
@router.get("/login")
async def login_page(request: Request):
	return templates.TemplateResponse(request, "auth/login.html", {"user": get_current_user(request)})

# TODO: POST /login、GET /logout、GET/POST /register、管理員審核帳號
