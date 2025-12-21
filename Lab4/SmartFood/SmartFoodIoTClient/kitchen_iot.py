import json
import time
import requests

def load_cfg():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def login(base_url, email, password):
    r = requests.post(f"{base_url}/api/login", json={"email": email, "password": password}, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data["access_token"]

def get_orders(base_url, token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{base_url}/api/admin/orders", headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def get_items_expanded(base_url, order_id):
    r = requests.get(f"{base_url}/api/order/{order_id}/items-expanded", timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    cfg = load_cfg()
    base_url = cfg["base_url"].rstrip("/")
    poll_sec = int(cfg.get("poll_sec", 3))

    token = login(base_url, cfg["admin_email"], cfg["admin_password"])
    print("Kitchen IoT started.")

    seen_state = {} 

    def signature(details: dict):
        items = details.get("items", [])
        sig_items = tuple(sorted((int(it["dish_id"]), int(it["quantity"])) for it in items))
        total = float(details.get("total_price", 0.0))
        return (total, sig_items)

    while True:
        try:
            orders = get_orders(base_url, token)
            created = [o for o in orders if o.get("status") == "created"]

            created_ids = set(o["order_id"] for o in created)
            for oid in list(seen_state.keys()):
                if oid not in created_ids:
                    del seen_state[oid]

            for o in created:
                oid = o["order_id"]
                details = get_items_expanded(base_url, oid)
                sig = signature(details)

                if oid not in seen_state:
                    seen_state[oid] = sig
                    print("\n=== NEW ORDER ===")
                elif seen_state[oid] != sig:
                    seen_state[oid] = sig
                    print("\n=== UPDATED ORDER ===")
                else:
                    continue  

                print(f"order_id={oid}, table_id={o.get('table_id')}, total={details.get('total_price')}")
                for it in details.get("items", []):
                    print(f"- {it['dish_name']} x{it['quantity']} = {it['total_item_price']}")
                print("====================\n")

        except Exception as e:
            print("Error:", e)

        time.sleep(poll_sec)

if __name__ == "__main__":
    main()
