import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class Dish:
    dish_id: int
    dish_name: str
    price: float


class SmartTableClient:
    def __init__(self, base_url: str, table_id: int):
        self.base_url = base_url.rstrip("/")
        self.table_id = table_id

        self.menu: List[Dish] = []
        self.selected_index: int = 0

        self.order_id: Optional[int] = None
        self.locked: bool = False  

    def _get(self, path: str) -> Any:
        r = requests.get(f"{self.base_url}{path}", timeout=10)
        if r.status_code >= 400:
            try:
                return {"_error": r.json(), "_status": r.status_code}
            except Exception:
                return {"_error": r.text, "_status": r.status_code}
        return r.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        r = requests.post(f"{self.base_url}{path}", json=payload, timeout=10)
        if r.status_code >= 400:
            try:
                return {"_error": r.json(), "_status": r.status_code}
            except Exception:
                return {"_error": r.text, "_status": r.status_code}
        return r.json()

    def load_menu(self) -> None:
        data = self._get("/api/menu")
        if isinstance(data, dict) and "_error" in data:
            raise RuntimeError(f"Menu error: {data}")

        self.menu = [
            Dish(dish_id=int(d["dish_id"]), dish_name=str(d["dish_name"]), price=float(d["price"]))
            for d in data
        ]
        self.selected_index = 0

    def ensure_order_id(self) -> None:
        if self.order_id is not None:
            return

        active = self._get(f"/api/table/{self.table_id}/active-order")
        if isinstance(active, dict) and "_error" not in active:
            self.order_id = int(active["order_id"])
            return

        created = self._post("/api/order/create", {"table_id": self.table_id})
        if isinstance(created, dict) and "_error" in created:
            raise RuntimeError(f"Create order error: {created}")

        self.order_id = int(created["order_id"])

    def add_selected_item(self) -> str:
        if self.locked:
            return "LOCKED: you can`t add"

        if not self.menu:
            return "No menu"

        self.ensure_order_id()
        assert self.order_id is not None

        dish = self.menu[self.selected_index]
        resp = self._post(f"/api/order/{self.order_id}/add-item", {"dish_id": dish.dish_id, "quantity": 1})

        if isinstance(resp, dict) and "_error" in resp:
            return f"Error ADD: {resp}"

        return f"Added: {dish.dish_name} (+1)"

    def get_order_view(self) -> Dict[str, Any]:
        if self.order_id is None:
            active = self._get(f"/api/table/{self.table_id}/active-order")
            if isinstance(active, dict) and "_error" not in active:
                self.order_id = int(active["order_id"])
            else:
                return {"message": "There is no active order yet. Click ADD to create one."}

        assert self.order_id is not None
        data = self._get(f"/api/order/{self.order_id}/items-expanded")
        if isinstance(data, dict) and "_error" in data:
            return {"error": data}

        return data

    def show_menu_screen(self) -> None:
        print("\n" + "=" * 60)
        print(f"SmartTable IoT | table_id={self.table_id} | state={'LOCKED' if self.locked else 'DRAFT'}")
        print("Buttons: [U]Up  [D]Down  [A]Add  [V]View order  [S]Submit/Lock  [C]Call waiter  [Q]Quit")
        print("-" * 60)

        if not self.menu:
            print("(The menu is empty.)")
            return

        start = max(0, self.selected_index - 2)
        end = min(len(self.menu), start + 5)

        for i in range(start, end):
            mark = ">" if i == self.selected_index else " "
            d = self.menu[i]
            print(f"{mark} {d.dish_id}. {d.dish_name} — {d.price:.2f}")

        if self.order_id:
            print(f"\nCurrent order_id: {self.order_id}")

    def show_order_screen(self) -> None:
        print("\n" + "=" * 60)
        print(f"ORDER VIEW | table_id={self.table_id} | state={'LOCKED' if self.locked else 'DRAFT'}")
        print("Buttons: [B]Back  [S]Submit/Lock  [C]Call waiter  [Q]Quit")
        print("-" * 60)

        data = self.get_order_view()
        if "message" in data:
            print(data["message"])
            return

        if "error" in data:
            print("Error:", data["error"])
            return

        items = data.get("items", [])
        if not items:
            print("The order is empty.")
        else:
            for it in items:
                print(f"- {it['dish_name']}  x{it['quantity']}  "
                      f"({float(it['unit_price']):.2f})  = {float(it['total_item_price']):.2f}")

        print("-" * 60)
        print(f"Total: {float(data.get('total_price', 0.0)):.2f}")
        print(f"order_id: {data.get('order_id')} | status: {data.get('status')}")

    def call_waiter(self) -> str:
        return "The waiter has been called ✅"


def load_config() -> Dict[str, Any]:
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_config()
    base_url = cfg.get("base_url", "http://127.0.0.1:5000")
    table_id = int(cfg.get("table_id", 1))

    raw = input(f"Enter table_id (Enter = {table_id}): ").strip()
    if raw:
        table_id = int(raw)

    client = SmartTableClient(base_url, table_id)

    # завантажуємо меню
    try:
        client.load_menu()
    except Exception as e:
        print("Failed to load menu:", e)
        print("Check that the backend is running and /api/menu is working.")
        return

    screen = "menu"
    while True:
        if screen == "menu":
            client.show_menu_screen()
            cmd = input("Command: ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "u":
                if client.menu:
                    client.selected_index = (client.selected_index - 1) % len(client.menu)
            elif cmd == "d":
                if client.menu:
                    client.selected_index = (client.selected_index + 1) % len(client.menu)
            elif cmd == "a":
                print(client.add_selected_item())
            elif cmd == "v":
                screen = "order"
            elif cmd == "s":
                if client.order_id is None:
                    print("There is no active order. Please click ADD first.")
                else:
                    resp = client._post(f"/api/order/{client.order_id}/submit", {})
                    if isinstance(resp, dict) and "_error" in resp:
                        print("Error submit:", resp)
                    else:
                        client.locked = True
                        print("The order is confirmed and sent to the kitchen. (LOCKED)")
            elif cmd == "c":
                print(client.call_waiter())
            else:
                print("Unknown command.")
        else:
            client.show_order_screen()
            cmd = input("Command: ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "b":
                screen = "menu"
            elif cmd == "s":
                client.locked = True
                print("Order confirmed (LOCKED).")
            elif cmd == "c":
                print(client.call_waiter())
            else:
                print("Unknown command.")


if __name__ == "__main__":
    main()
