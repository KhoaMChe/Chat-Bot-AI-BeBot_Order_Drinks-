from flask import Flask, request, jsonify
import re
from db import update_order_status, get_order
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

def send_telegram(chat_id, msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": msg
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("PAYMENT CALLBACK:", data)

    try:
        if data.get("code") == "00":
            desc = data["data"]["description"]

            match = re.search(r"ORDER(\d+)", desc)
            if match:
                order_id = int(match.group(1))

                # update status
                update_order_status(order_id, "paid")

                # lấy thông tin order để biết chat_id
                order = get_order(order_id)

                if order:
                    chat_id = order[4]  # tuỳ thứ tự cột DB
                    name = order[5]

                    send_telegram(
                        chat_id,
                        f"✅ Thanh toán thành công!\n\n🧾 Đơn #{order_id}\n👤 {name}\n💰 Đã thanh toán xong"
                    )

                print(f"✅ Order {order_id} paid")

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return jsonify({"message": "ok"})

if __name__ == "__main__":
    app.run(port=5000)