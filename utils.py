import pandas as pd

def load_menu():
    return pd.read_csv("menu.csv")

def menu_to_text(df):
    lines = []
    for _, r in df.iterrows():
        if str(r["available"]).lower() == "true":
            lines.append(
                f"{r['item_id']} - {r['name']} "
                f"(M:{r['price_m']}đ, L:{r['price_l']}đ)"
            )
    return "\n".join(lines)


def calc_total(order, df):
    total = 0

    for item in order["items"]:
        row = df[df["item_id"] == item["item_id"]]

        if row.empty:
            continue

        row = row.iloc[0]

        if str(row["available"]).lower() != "true":
            continue

        size = item.get("size", "M")

        if size == "L":
            price = row["price_l"]
        else:
            price = row["price_m"]

        total += price * item["quantity"]

    return total
