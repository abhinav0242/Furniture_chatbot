import os
import re
import random
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient

# ML imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# ======================================================
# CONFIG
# ======================================================

MONGO_URI = os.getenv("MONGO_URI")
API_KEY = os.getenv("API_KEY")

client = MongoClient(MONGO_URI)
db = client["furniture_db"]

orders_col = db["orders"]
agents_col = db["agents"]
sessions_col = db["sessions"]

app = FastAPI(title="Furniture Chatbot")

# ======================================================
# ML INTENT MODEL
# ======================================================

training_sentences = [
    "track my order",
    "where is my order",
    "order status",
    "cancel my order",
    "I want to cancel",
    "talk to agent",
    "connect me to support",
    "I need help"
]

training_labels = [
    "track",
    "track",
    "track",
    "cancel",
    "cancel",
    "agent",
    "agent",
    "agent"
]

vectorizer = TfidfVectorizer()
X_train = vectorizer.fit_transform(training_sentences)

model = MultinomialNB()
model.fit(X_train, training_labels)

def predict_intent(text):
    vec = vectorizer.transform([text.lower()])
    return model.predict(vec)[0]

# ======================================================
# REQUEST MODEL
# ======================================================

class ChatRequest(BaseModel):
    user_id: str
    message: str

# ======================================================
# AUTH
# ======================================================

def verify_api_key(x_api_key: str):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# ======================================================
# SESSION
# ======================================================

def get_session(user_id):
    session = sessions_col.find_one({"user_id": user_id})
    if not session:
        sessions_col.insert_one({
            "user_id": user_id,
            "state": "MAIN_MENU",
            "selected_order": None
        })
        return {"state": "MAIN_MENU", "selected_order": None}
    return session

def update_session(user_id, state=None, selected_order=None):
    update_data = {}
    if state:
        update_data["state"] = state
    if selected_order is not None:
        update_data["selected_order"] = selected_order

    sessions_col.update_one(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True
    )

# ======================================================
# BUSINESS LOGIC
# ======================================================

def show_main_menu():
    return {
        "type": "menu",
        "message": "How can I help you?",
        "options": ["Orders", "Talk to Agent"]
    }

def list_orders(user_id):
    orders = list(
        orders_col.find(
            {"user_id": user_id},
            {"_id": 0, "order_id": 1, "status": 1}
        )
    )

    if not orders:
        return {"message": "You have no orders."}

    return {
        "type": "order_list",
        "message": "Here are your orders:",
        "orders": orders
    }

def track_order(order_id):
    order = orders_col.find_one({"order_id": order_id})
    if not order:
        return {"error": "Order not found"}

    return {
        "type": "order_status",
        "order_id": order_id,
        "status": order.get("status"),
        "delivery_date": order.get("delivery_date")
    }

def cancel_order(order_id):
    orders_col.update_one(
        {"order_id": order_id},
        {"$set": {"status": "cancelled"}}
    )
    return {"message": f"Order {order_id} has been cancelled."}

def connect_agent():
    agent = agents_col.find_one({"status": "available"})
    if not agent:
        return {"message": "No agent available"}

    agents_col.update_one(
        {"agent_id": agent["agent_id"]},
        {"$set": {"status": "busy"}}
    )

    return {
        "type": "agent_assigned",
        "agent_name": agent["name"],
        "contact": agent.get("phone")
    }

# ======================================================
# HYBRID PROCESSOR
# ======================================================

def extract_order_id(message):
    match = re.search(r"O\d+", message.upper())
    return match.group() if match else None

def process_message(user_id, message):

    session = get_session(user_id)
    state = session["state"]
    selected_order = session.get("selected_order")

    if message.lower() in ["start", "menu"]:
        update_session(user_id, state="MAIN_MENU", selected_order=None)
        return show_main_menu()

    if state == "MAIN_MENU":
        if message == "Orders":
            update_session(user_id, state="VIEWING_ORDERS")
            return list_orders(user_id)

        if message == "Talk to Agent":
            return connect_agent()

    if state == "VIEWING_ORDERS":
        update_session(user_id, state="ORDER_SELECTED", selected_order=message)
        return {
            "type": "order_actions",
            "order_id": message,
            "options": ["Track", "Cancel"]
        }

    if state == "ORDER_SELECTED":
        if message == "Track":
            return track_order(selected_order)
        if message == "Cancel":
            return cancel_order(selected_order)

    intent = predict_intent(message)
    order_id = extract_order_id(message)

    if intent == "track" and order_id:
        return track_order(order_id)

    if intent == "cancel" and order_id:
        return cancel_order(order_id)

    if intent == "agent":
        return connect_agent()

    return show_main_menu()

# ======================================================
# ENDPOINTS
# ======================================================

@app.post("/chat")
async def chat(request: ChatRequest, x_api_key: str = Header(None)):
    verify_api_key(x_api_key)
    return process_message(request.user_id, request.message)

@app.get("/")
def health():
    return {"status": "Hybrid Chatbot Running"}
