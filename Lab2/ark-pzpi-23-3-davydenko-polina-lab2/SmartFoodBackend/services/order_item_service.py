from models.models import Dish, OrderItem
from config import db

def add_order_item(order_id, dish_id, quantity):
    dish = Dish.query.get(dish_id)
    unit_price = dish.price               # ← автоматично беремо
    total_item_price = unit_price * quantity

    item = OrderItem(
        order_id=order_id,
        dish_id=dish_id,
        quantity=quantity,
        unit_price=unit_price,
        total_item_price=total_item_price
    )
    db.session.add(item)
    db.session.commit()
    return item

def get_items_by_order(order_id):
    return OrderItem.query.filter_by(order_id=order_id).all()

def delete_order_item(order_id, dish_id):
    item = OrderItem.query.get((order_id, dish_id))
    db.session.delete(item)
    db.session.commit()
