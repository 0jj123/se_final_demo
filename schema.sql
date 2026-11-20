-- schema.sql（共用，修改前先在群組說）
-- 建立：psql -U postgres -d se_final -f schema.sql

-- ===== 共用 =====
CREATE TABLE IF NOT EXISTS users (
	id            SERIAL PRIMARY KEY,
	username      VARCHAR(50) UNIQUE NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	role          VARCHAR(20) NOT NULL DEFAULT 'user'    CHECK (role IN ('admin', 'teacher', 'user')),
	status        VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved'))
);

-- 模組一負責增刪改，其他模組只讀（欄位待模組一確認）
CREATE TABLE IF NOT EXISTS rooms (
	id          SERIAL PRIMARY KEY,
	code        VARCHAR(20) UNIQUE NOT NULL,   -- 教室編號
	name        VARCHAR(100) NOT NULL,
	floor       INT,
	capacity    INT,
	description TEXT,
	pano_url    VARCHAR(255)                   -- 360 全景照片
);

-- ===== 模組一：空間查詢 =====

-- ===== 模組二：預約借用 =====

-- ===== 模組三：排課 =====
