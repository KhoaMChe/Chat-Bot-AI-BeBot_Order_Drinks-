import sqlite3
import pandas as pd
import time
import json

DB_NAME = "db.sqlite3"


# ==============================
#  KẾT NỐI DB
# ==============================
def get_conn():
    return sqlite3.connect(DB_NAME)


# ==============================
#  TẠO BẢNG
# ==============================
def init_db():
    conn = get_conn()
    c = conn.cursor()

    # bảng menu
    c.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        item_id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        price_m INTEGER,
        price_l INTEGER,
        available BOOLEAN
    )
    """)

    # bảng đơn hàng
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        total INTEGER,
        status TEXT,
        chat_id TEXT,
        customer_name TEXT,
        phone TEXT,
        address TEXT,
        created_at INTEGER 
        
    )
    """)

    conn.commit()
    conn.close()


# ==============================
#  LOAD CSV → DB
# ==============================
def load_menu_from_csv(csv_file="menu.csv"):
    try:
        df = pd.read_csv(csv_file, encoding="utf-8")

        conn = get_conn()
        c = conn.cursor()

        for _, row in df.iterrows():
            c.execute("""
            INSERT OR REPLACE INTO menu 
            (item_id, name, description, price_m, price_l, available)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(row["item_id"]).upper(),
                row["name"],
                row["description"],
                int(row["price_m"]),
                int(row["price_l"]),
                1 if str(row["available"]).lower() == "true" else 0
            ))

        conn.commit()
        conn.close()

        print("✅ Load menu thành công")
        return df

    except Exception as e:
        print("❌ LOAD MENU ERROR:", e)
        return None


# ==============================
# 📄 LẤY MENU DẠNG TEXT (CHO AI)
# ==============================
def get_menu_text():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    SELECT item_id, name, price_m, price_l 
    FROM menu 
    WHERE available = 1
    """)

    rows = c.fetchall()
    conn.close()

    if not rows:
        return "Menu đang trống"

    text = ""
    for r in rows:
        text += f"{r[0]} - {r[1]} (M:{r[2]}, L:{r[3]})\n"

    return text


# ==============================
#  TÍNH TIỀN
# ==============================
def calculate_total(order):
    conn = get_conn()
    c = conn.cursor()

    # load toàn bộ menu vào dict (nhanh hơn)
    c.execute("SELECT item_id, price_m, price_l FROM menu")
    menu_map = {row[0]: (row[1], row[2]) for row in c.fetchall()}

    conn.close()

    total = 0

    for item in order.get("items", []):
        item_id = item.get("item_id", "").upper()
        size = item.get("size", "").upper()
        quantity = item.get("quantity", 0)

        # validate
        if quantity <= 0:
            print("⚠️ quantity lỗi:", item)
            continue

        if item_id not in menu_map:
            print("⚠️ item không tồn tại:", item_id)
            continue

        price_m, price_l = menu_map[item_id]

        if size == "M":
            price = price_m
        elif size == "L":
            price = price_l
        else:
            print("⚠️ size lỗi:", item)
            continue

        total += price * quantity

    return total


# ==============================
#  LƯU ĐƠN
# ==============================

def save_order(content, total, chat_id, name, phone, address):
    conn = get_conn()
    c = conn.cursor()

    created_at = int(time.time())

    c.execute("""
    INSERT INTO orders 
    (content, total, status, chat_id, customer_name, phone, address, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        json.dumps(content),   # 👈 QUAN TRỌNG
        total,
        "pending",
        chat_id,
        name,
        phone,
        address,
        created_at
    ))

    conn.commit()
    order_id = c.lastrowid
    conn.close()

    return order_id

# ==============================
#  UPDATE TRẠNG THÁI
# ==============================
def update_order_status(order_id, status):
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, order_id)
    )

    conn.commit()
    conn.close()

    print(f"🔄 Order {order_id} -> {status}")


# ==============================
#  LẤY ĐƠN
# ==============================
def get_order(order_id):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    row = c.fetchone()

    conn.close()
    return row


# ==============================
#  LẤY TẤT CẢ ĐƠN
# ==============================
def get_all_orders():
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = c.fetchall()

    conn.close()
    return rows


def cleanup_orders():
    conn = get_conn()
    c = conn.cursor()

    expire_time = int(time.time()) - 300  # 5 phút

    c.execute("""
    UPDATE orders
    SET status = 'expired'
    WHERE status = 'pending'
    AND created_at < ?
    """, (expire_time,))

    conn.commit()
    conn.close()

    print("🧹 Cleaned expired orders")

