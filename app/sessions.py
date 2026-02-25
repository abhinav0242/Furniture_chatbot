from app.database import sessions_col

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