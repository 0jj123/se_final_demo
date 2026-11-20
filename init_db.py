# init_db.py：建立資料庫 + 匯入 schema.sql（Mac / Windows 通用）
# 用法：uv run --with-requirements requirements.txt python init_db.py
import os
import sys

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from db import load_env

load_env()
url = os.environ.get("DATABASE_URL")
if not url:
	sys.exit("❌ 找不到 .env 或裡面沒有 DATABASE_URL，請先做 README 步驟 5")

dbname = conninfo_to_dict(url)["dbname"]

try:
	# 1. 先連到內建的 postgres 資料庫，檢查 / 建立專案資料庫
	with psycopg.connect(make_conninfo(url, dbname="postgres"), autocommit=True) as conn:
		exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)).fetchone()
		if exists:
			print(f"✅ 資料庫 {dbname} 已存在")
		else:
			conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
			print(f"✅ 已建立資料庫 {dbname}")

	# 2. 連進專案資料庫，匯入 schema.sql
	with open("schema.sql", encoding="utf-8") as f:
		schema = f.read()
	with psycopg.connect(url) as conn:
		conn.execute(schema)
		tables = conn.execute(
			"SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
		).fetchall()
	print("✅ 已匯入 schema.sql，目前的資料表：", ", ".join(t[0] for t in tables))

except psycopg.OperationalError as e:
	msg = str(e)
	if "password authentication failed" in msg:
		sys.exit("❌ 密碼錯誤：請檢查 .env 裡的密碼（密碼有 @ 要寫成 %40）")
	if "Connection refused" in msg or "could not connect" in msg or "connection failed" in msg:
		sys.exit(f"❌ 連不上 PostgreSQL：請確認 PostgreSQL 有安裝並啟動\n{msg}")
	sys.exit(f"❌ 連線失敗：{msg}")
