from models.models import Order, OrderItem, OrderStatus
from config import db
from datetime import datetime

def create_order(table_id):
    order = Order(table_id=table_id, created_at=datetime.now(), status=OrderStatus.created, total_price=0)
    db.session.add(order)
    db.session.commit()
    return order

def get_order_by_id(order_id):
    return Order.query.get(order_id)

def update_order_status(order_id, status):
    if status not in OrderStatus._value2member_map_:
        raise ValueError("Неприпустимий статус")
    order = Order.query.get(order_id)
    order.status = OrderStatus(status)
    db.session.commit()
    return order

def calculate_total(order_id):
    items = OrderItem.query.filter_by(order_id=order_id).all()
    total = sum(item.total_item_price for item in items)
    order = Order.query.get(order_id)
    order.total_price = total
    db.session.commit()
    return order.total_price
