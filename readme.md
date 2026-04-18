# 🤖 Telegram Order Bot (PayOS Integration)

## 🚀 Giới thiệu

Đây là một chatbot Telegram hỗ trợ:

* 📋 Hiển thị menu
* 🛒 Nhận order tự động bằng AI
* 💰 Tính tiền
* 💳 Tạo link thanh toán qua PayOS
* 📱 Gửi QR code cho khách
* 🔔 Nhận webhook khi thanh toán thành công
* 📦 Quản lý đơn hàng cho người bán

---

## 🧠 Flow hoạt động

1. Khách nhắn:

   * "menu" → bot gửi menu
   * "trà sữa size M 2 ly" → bot parse order

2. Bot xử lý:

   * Nếu thiếu size → hỏi lại
   * Nếu đủ → hiển thị đơn + tổng tiền

3. Khách nhập:

```
Tên | SĐT | Địa chỉ
```

4. Bot:

* Xác nhận thanh toán
* Tạo link PayOS
* Gửi QR code + link

5. Sau khi thanh toán:

* Webhook nhận callback
* Update DB → `paid`
* Gửi thông báo Telegram

---

## 🛠️ Công nghệ sử dụng

* Python
* python-telegram-bot
* Flask (webhook)
* SQLite
* PayOS API
* qrcode

---

## 📂 Cấu trúc project

```
project/
│── ai.py               # Gọi API AI và set luật
│── bot.py              # Telegram bot chính
│── payment.py          # Tạo link PayOS
│── webhook.py          # Nhận callback thanh toán
│── db.py               # Xử lý database
│── menu.csv            # Menu sản phẩm
│── db.sqlite3          # Database
│── .env                # Chứa secret key
│── requirements.txt
│── utils.py            # Load menu và tính tiền

```

---

## ⚙️ Cài đặt

### 1. Clone project

```
git clone <repo>
cd project
```

### 2. Tạo virtual environment

```
python -m venv .venv
.venv\Scripts\activate
```

### 3. Cài thư viện

```
pip install -r requirements.txt
```

### 4. Setup database

```python
init_db()
load_menu_from_csv("menu.csv")
```

---

## ▶️ Chạy bot

```
python bot.py
```

---

## 🌐 Chạy webhook (production)

```
python webhook.py
```

## 📦 Xem đơn hàng

Trong Telegram:

```
/orders
```

Hiển thị:

* Tên khách
* SĐT
* Địa chỉ
* Món đã đặt
* Trạng thái thanh toán

---

## ⏳ Auto huỷ đơn

* Sau 5 phút chưa thanh toán: sẽ hủy đơn 

## 👨‍💻 Tác giả

* KhoaMChe

---

## 📌 Ghi chú

Project này là nền tảng rất tốt để phát triển:

* SaaS order bot
* POS mini cho quán nhỏ
* Startup đồ ăn / nước uống

