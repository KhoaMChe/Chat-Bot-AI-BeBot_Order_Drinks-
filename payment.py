# from payos import PayOS
# import time

# payOS = PayOS(
#     client_id="2dc60f96-597b-49ca-84c3-c9fa090c5afa",
#     api_key="d39ad2b7-449b-4e12-a18b-bc32498c3ae7",
#     checksum_key="41c3a9a0c0e761874eb86566187e918eafb3c390c546fa77fbb6c8499e3907b2"
# )


# def create_payment_link(order_id, amount):
#     try:
#         amount = int(amount)
#         order_code = int(time.time() * 1000)

#         data = {
#             "orderCode": order_code,
#             "amount": amount,
#             "description": f"ORDER{order_id}",
#             "items": [
#                 {
#                     "name": f"Order {order_id}",
#                     "quantity": 1,
#                     "price": amount
#                 }
#             ],
#             "returnUrl": "https://example.com/success",
#             "cancelUrl": "https://example.com/cancel"
#         }

#         print("🚀 USING DICT VERSION")

#         response = payOS.createPaymentLink(data)

#         return {
#             "checkoutUrl": response.checkoutUrl,
#             "qrCode": response.qrCode
#         }

#     except Exception as e:
#         print("❌ PAYOS ERROR:", e)
#         return None


import requests
import time
import hashlib
import hmac
import json
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
API_KEY = os.getenv("PAYOS_API_KEY")
CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")

BASE_URL = "https://api-merchant.payos.vn/v2/payment-requests"


def create_signature(data):
    raw = (
        f"amount={data['amount']}&"
        f"cancelUrl={data['cancelUrl']}&"
        f"description={data['description']}&"
        f"orderCode={data['orderCode']}&"
        f"returnUrl={data['returnUrl']}"
    )

    print("🔐 RAW SIGN:", raw)

    return hmac.new(
        CHECKSUM_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()



def create_payment_link(order_id, amount):
    try:
        amount = int(amount)
        order_code = int(time.time() * 1000)

        data = {
            "orderCode": order_code,
            "amount": amount,
            "description": f"ORDER{order_id}",
            "returnUrl": "https://example.com/success",
            "cancelUrl": "https://example.com/cancel"
        }

        signature = create_signature(data)

        payload = {
            **data,
            "signature": signature
        }

        headers = {
            "x-client-id": CLIENT_ID,
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }

        print("🚀 CALL PAYOS API DIRECT")

        res = requests.post(BASE_URL, json=payload, headers=headers)

        print("STATUS:", res.status_code)
        print("RESPONSE:", res.text)

        result = res.json()

        if result["code"] == "00":
            return {
                "checkoutUrl": result["data"]["checkoutUrl"],
                "qrCode": result["data"]["qrCode"]
            }

        return None

    except Exception as e:
        print("❌ PAYOS ERROR:", e)
        return None
