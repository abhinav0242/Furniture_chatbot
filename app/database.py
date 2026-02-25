from pymongo import MongoClient
from app.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["furniture_db"]

orders_col = db["orders"]
agents_col = db["agents"]
sessions_col = db["sessions"]