
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
