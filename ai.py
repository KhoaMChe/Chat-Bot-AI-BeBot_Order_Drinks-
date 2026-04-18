from groq import Groq
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("AI_API_KEY"))

def parse_order(message, menu_text):
    prompt = f"""
Chỉ trả JSON hợp lệ.

Format:
{{
  "items": [
    {{
      "item_id": "",
      "quantity": 0,
      "size": "M hoặc L"
    }}
  ]
}}

Luật:
- Chỉ dùng item_id trong menu
- Không giải thích
- Không trả menu
- Không nói chuyện
- Nếu không hiểu → trả {{"items": []}}

Menu:
{menu_text}

Tin nhắn: {message}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON API. Only output JSON. No text."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        text = response.choices[0].message.content

        print("AI RAW:", text)

        match = re.search(r'\{.*\}', text, re.DOTALL)

        if match:
            try:
                result = json.loads(match.group())

                # 🔥 đảm bảo luôn có items
                if "items" not in result:
                    return {"items": []}

                return result
            except:
                pass

        return {"items": []}

    except Exception as e:
        print("AI ERROR:", e)
        return {"items": []}