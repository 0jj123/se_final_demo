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

-- 模組二：空間／物品預約借用

-- 1. 教室預約資料表
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL REFERENCES users(id),
    room_id INTEGER NOT NULL REFERENCES rooms(id),

    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),

    review_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    checked_out_at TIMESTAMP,
    returned_at TIMESTAMP,

    CHECK (start_time < end_time)
);


-- 2. 可借用物品資料表
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,

    name VARCHAR(100) UNIQUE NOT NULL,

    total_quantity INTEGER NOT NULL DEFAULT 1
        CHECK (total_quantity > 0)
);


-- 3. 預約與借用物品的關聯資料表
CREATE TABLE IF NOT EXISTS booking_items (
    id SERIAL PRIMARY KEY,

    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    item_id INTEGER NOT NULL REFERENCES items(id),

    quantity INTEGER NOT NULL DEFAULT 1
        CHECK (quantity > 0),

    checked_out_at TIMESTAMP,
    returned_at TIMESTAMP,

    UNIQUE (booking_id, item_id),

    CHECK (
        returned_at IS NULL
        OR (
            checked_out_at IS NOT NULL
            AND returned_at >= checked_out_at
        )
    )
);


-- 4. 更新已經存在的預約資料表
ALTER TABLE bookings
    ADD COLUMN IF NOT EXISTS checked_out_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS returned_at TIMESTAMP;


-- ===== 模組三：排課 =====
