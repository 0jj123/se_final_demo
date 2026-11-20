# db.py（共用，修改前先在群組說）
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row


def load_env(path=".env"):
	"""讀取 .env 到環境變數（避免密碼寫死在程式裡）"""
	if not os.path.exists(path):
		return
	with open(path, encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if line and not line.startswith("#") and "=" in line:
				key, value = line.split("=", 1)
				os.environ.setdefault(key.strip(), value.strip())


load_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
	app.state.pool = AsyncConnectionPool(
		conninfo=os.environ["DATABASE_URL"],
		kwargs={"row_factory": dict_row},
		open=False,
	)
	await app.state.pool.open()
	print("✅ Connected to DB")
	yield
	await app.state.pool.close()
	print("🛑 Disconnected from DB")


async def getDB(request: Request):
	async with request.app.state.pool.connection() as conn:
		yield conn
