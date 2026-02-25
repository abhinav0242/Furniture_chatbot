import re
from app.database import orders_col, agents_col
from app.ml_model import predict_intent
from app.session import get_session, update_session

def extract_order_id(message):
    match = re.search(r"O\d+", message.upper())
    return match.group() if match else None

def show_menu():
    return {
        "type": "menu",
        "message": "How can I help you?",
        "options": ["Orders", "Talk to Agent"]
    }

def process_message(user_id, message):

    session = get_session(user_id)
    state = session["state"]
    selected_order = session.get("selected_order")

    if message.lower() in ["start", "menu"]:
        update_session(user_id, state="MAIN_MENU", selected_order=None)
        return show_menu()

    if state == "MAIN_MENU":
        if message == "Orders":
            update_session(user_id, state="VIEWING_ORDERS")
            orders = list(
                orders_col.find(
                    {"user_id": user_id},
                    {"_id": 0, "order_id": 1, "status": 1}
                )
            )
            return {"type": "order_list", "orders": orders}

        if message == "Talk to Agent":
            agent = agents_col.find_one({"status": "available"})
            return {"type": "agent", "agent": agent}

    # ML fallback
    intent = predict_intent(message)
    order_id = extract_order_id(message)

    if intent == "track" and order_id:
        order = orders_col.find_one({"order_id": order_id})
        return {"type": "order_status", "order": order}

    if intent == "cancel" and order_id:
        orders_col.update_one(
            {"order_id": order_id},
            {"$set": {"status": "cancelled"}}
        )
        return {"message": f"{order_id} cancelled"}

    if intent == "agent":
        agent = agents_col.find_one({"status": "available"})
        return {"type": "agent", "agent": agent}

    return show_menu()