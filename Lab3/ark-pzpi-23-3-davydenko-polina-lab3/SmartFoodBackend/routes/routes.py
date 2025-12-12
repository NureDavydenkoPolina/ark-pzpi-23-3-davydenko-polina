from flask import request, Response, jsonify
import json
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity

from services.dish_service import get_all_dishes
from services.order_service import create_order, get_order_by_id, update_order_status, calculate_total
from services.order_item_service import add_order_item, get_items_by_order, delete_order_item
from services.user_service import verify_user
from auth.role_required import role_required

def init_routes(app):

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json()
        user = verify_user(data["email"], data["password"])
        if not user:
            return jsonify({"error": "Невірна пошта або пароль"}), 401

        payload = {"id": user.user_id, "role": user.role_id}
        token = create_access_token(identity=json.dumps(payload))

        return jsonify({"access_token": token})

    @app.route("/api/menu", methods=["GET"])
    def menu():
        dishes = get_all_dishes()
        result = []
        for d in dishes:
            result.append({
                "dish_id": d.dish_id,
                "dish_name": d.dish_name,
                "price": float(d.price),
                "description": d.description
            })
        return Response(json.dumps(result, ensure_ascii=False, indent=4),
                        content_type="application/json; charset=utf-8")

    @app.route("/api/order/create", methods=["POST"])
    def order_create():
        data = request.get_json()
        order = create_order(data["table_id"])
        return jsonify({"order_id": order.order_id, "status": order.status.value})

    @app.route("/api/order/<int:order_id>", methods=["GET"])
    def order_details(order_id):
        order = get_order_by_id(order_id)
        return jsonify({
            "order_id": order.order_id,
            "table_id": order.table_id,
            "status": order.status.value,
            "total_price": order.total_price
        })
    
    @app.route("/api/order/<int:order_id>/add-item", methods=["POST"])
    def add_item(order_id):
        data = request.get_json()
        item = add_order_item(order_id, data["dish_id"], data["quantity"])
        return jsonify({
            "message": "Страву додано",
            "dish_id": item.dish_id,
            "unit_price": item.unit_price,
            "total_item_price": item.total_item_price
        })


    @app.route("/api/order/<int:order_id>/items", methods=["GET"])
    @role_required(2, 3)
    @jwt_required()
    def order_items(order_id):
        items = get_items_by_order(order_id)
        result = []
        for i in items:
            result.append({
                "dish_id": i.dish_id,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "total_item_price": i.total_item_price
            })
        return jsonify(result)

    @app.route("/api/order/<int:order_id>/status", methods=["PUT"])
    @jwt_required()
    def update_status(order_id):
        data = request.get_json()
        identity = json.loads(get_jwt_identity())
        role = identity["role"]
        new_status = data["status"]

        # waiter може тільки delivered
        if role == 2 and new_status != "delivered":
            return jsonify({"error": "Офіціант може встановити лише статус delivered"}), 403

        if role == 3 and new_status == "delivered":
            return jsonify({"error": "Кухар не може встановити статус delivered"}), 403

        updated = update_order_status(order_id, new_status)

        return jsonify({
            "order_id": updated.order_id,
            "new_status": updated.status.value
        })

    @app.route("/api/order/<int:order_id>/total", methods=["GET"])
    def order_total(order_id):
        total = calculate_total(order_id)
        return jsonify({"order_id": order_id, "total_price": total})

    @app.route("/api/order/<int:order_id>/delete-item", methods=["DELETE"])
    def delete_item(order_id):
        data = request.get_json()
        delete_order_item(order_id, data["dish_id"])
        return jsonify({"message": "Позицію видалено", "dish_id": data["dish_id"]})
    
    
