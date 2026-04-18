from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
# from utils_qr import generate_qr_image
import qrcode
# import urllib.parse
import json
import qrcode
from io import BytesIO

# from db import cleanup_orders

from ai import parse_order
from utils import load_menu, menu_to_text, calc_total

from db import init_db, save_order,load_menu_from_csv
from payment import create_payment_link
import sqlite3
from telegram.ext import CommandHandler
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

init_db()
load_menu_from_csv("menu.csv")

menu_df = load_menu()
menu_text = menu_to_text(menu_df)
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(menu_text)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    # ===== STEP 1: nếu đang chờ size =====
    if context.user_data.get("pending_size"):
        size = text.upper()

        if size not in ["M", "L"]:
            await update.message.reply_text("Chỉ chọn M hoặc L thôi nhé")
            return

        order = context.user_data["order"]

        for item in order["items"]:
            item["size"] = size

        context.user_data["pending_size"] = False
        context.user_data["order"] = order

        # tiếp tục xuống confirm

    # ===== STEP 2: nếu đang confirm =====
    # ===== STEP 2.5: nhập thông tin khách =====
    elif context.user_data.get("waiting_info"):
        try:
            # format: tên | sdt | địa chỉ
            name, phone, address = text.split("|")

            context.user_data["customer"] = {
                "name": name.strip(),
                "phone": phone.strip(),
                "address": address.strip()
            }

            context.user_data["waiting_info"] = False
            context.user_data["confirming_payment"] = True

            await update.message.reply_text(
                "Xác nhận thanh toán? (yes/no)"
            )
            return

        except:
            await update.message.reply_text(
                "❌ Nhập sai format\nVD: Khoa | 0123456789 | Bình Dương"
            )
            return

    elif text in ["yes", "no"] and context.user_data.get("confirming_payment"):
        if text == "yes":
            order = context.user_data["order"]
            total = context.user_data["total"]
            customer = context.user_data["customer"]

            # 🔥 lưu đầy đủ info
            full_data = {
                "order": order,
                "customer": customer
            }

            # order_id = save_order(str(full_data), total)
            chat_id = update.effective_chat.id

            order_id = save_order(
                json.dumps(full_data),
                int(total),
                chat_id,
                customer["name"],
                customer["phone"],
                customer["address"]
            )
            payment = create_payment_link(order_id, total)
            if not payment:
                await update.message.reply_text("❌ Lỗi tạo thanh toán")
                return

            checkout_url = payment["checkoutUrl"]
            qr_code = payment["qrCode"]

            # tạo QR image
            qr = qrcode.make(qr_code)

            bio = BytesIO()
            bio.name = "qr.png"
            qr.save(bio, "PNG")
            bio.seek(0)

            await update.message.reply_photo(
                photo=bio,
                caption=f"""
    💳 Thanh toán đơn hàng

    👤 {customer['name']}
    📞 {customer['phone']}
    📍 {customer['address']}

    💰 Số tiền: {total}đ

    📌 Nội dung: ORDER{order_id}

    👉 Link:
    {checkout_url}
    """
            )

        else:
            await update.message.reply_text("❌ Đã hủy đơn")

        context.user_data.clear()
        return


    # ===== STEP 3: parse đơn mới =====
    else:
        order = parse_order(text, menu_text)

        if not order or "items" not in order or not order["items"]:
            await update.message.reply_text("❌ Không hiểu, bạn đặt lại giúp nhé")
            return

        # normalize data
        for item in order["items"]:
            item["item_id"] = item["item_id"].upper()

            if "size" in item:
                item["size"] = item["size"].upper()
            else:
                item["size"] = None

        # check thiếu size
        for item in order["items"]:
            if item["size"] not in ["M", "L"]:
                context.user_data["order"] = order
                context.user_data["pending_size"] = True

                await update.message.reply_text("Bạn chọn size M hay L ạ?")
                return

        context.user_data["order"] = order


    # ===== STEP 4: tính tiền =====
    order = context.user_data["order"]
    total = calc_total(order, menu_df)

    context.user_data["total"] = total
    context.user_data["confirming"] = True

    # ===== STEP 5: hiển thị đơn =====
    reply = "🧾 Đơn của bạn:\n"

    for i in order["items"]:
        row_match = menu_df[menu_df["item_id"] == i["item_id"]]

        if row_match.empty:
            await update.message.reply_text(f"❌ Món {i['item_id']} không tồn tại")
            return

        row = row_match.iloc[0]
        reply += f"- {row['name']} ({i['size']}) x{i['quantity']}\n"

    reply += f"\n💰 Tổng: {total}đ"
    reply += "\n\nNhập thông tin (Tên | SĐT | Địa chỉ)"
    context.user_data["waiting_info"] = True

    await update.message.reply_text(reply)

# async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

#     # (tuỳ chọn) chặn người lạ
#     # if update.effective_user.id != OWNER_ID:
#     #     return

#     conn = sqlite3.connect("db.sqlite3")
#     c = conn.cursor()

#     c.execute("""
#         SELECT id, content, total, status, customer_name, phone, address
#         FROM orders
#         ORDER BY id DESC
#         LIMIT 20
#     """)

#     rows = c.fetchall()
#     conn.close()

#     text = "📦 DANH SÁCH ĐƠN HÀNG\n\n"

#     for r in rows:
#         order_id, content, total, status, name, phone, address = r

#         # parse JSON order
#         try:
#             items = json.loads(content)["items"]

#         except:
#             items = []

#         item_text = ""
#         for i in items:
#             item_text += f"- {i['item_id']} ({i['size']}) x{i['quantity']}\n"

#         text += f"""
# 🧾 Order #{order_id}
# 👤 {name}
# 📞 {phone}
# 📍 {address}

# 🛒 Đơn:
# {item_text}
# 💰 {total}đ
# 💳 {status}

# -------------------
# """

#     await update.message.reply_text(text)

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = sqlite3.connect("db.sqlite3")
    c = conn.cursor()

    # 🔥 load menu để map tên món
    c.execute("SELECT item_id, name FROM menu")
    menu_map = {row[0]: row[1] for row in c.fetchall()}

    # 🔥 lấy đơn hàng
    c.execute("""
        SELECT id, content, total, status, customer_name, phone, address
        FROM orders
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = c.fetchall()
    conn.close()

    text = "📦 DANH SÁCH ĐƠN HÀNG\n\n"

    for r in rows:
        order_id, content, total, status, name, phone, address = r

        # ===== parse JSON =====
        try:
            data = json.loads(content)
            if isinstance(data, str):
                data = json.loads(data)
            # hỗ trợ cả format cũ + mới
            if "order" in data:
                items = data["order"].get("items", [])
            else:
                items = data.get("items", [])

        except Exception as e:
            print("PARSE ERROR:", e)
            print("RAW CONTENT:", content)
            items = []

        # ===== build item text =====
        item_text = ""

        if not items:
            item_text = "⚠️ Không có dữ liệu món\n"
        else:
            for i in items:
                item_id = i.get("item_id", "")
                size = i.get("size", "?")
                quantity = i.get("quantity", 0)

                # map sang tên thật
                name_item = menu_map.get(item_id, item_id)

                item_text += f"- {name_item} ({size}) x{quantity}\n"

        # ===== format status đẹp =====
        status_map = {
            "pending": "⏳ Chờ thanh toán",
            "paid": "✅ Đã thanh toán",
            "expired": "❌ Hết hạn"
        }

        status_text = status_map.get(status, status)

        # ===== append text =====
        text += f"""
🧾 Order #{order_id}
👤 {name}
📞 {phone}
📍 {address}

🛒 Đơn:
{item_text}
💰 {total}đ
💳 {status_text}

-------------------
"""

    await update.message.reply_text(text)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # app.add_handler(MessageHandler(filters.TEXT, handle))
    app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle)
)
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(CommandHandler("orders", show_orders))


    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()





