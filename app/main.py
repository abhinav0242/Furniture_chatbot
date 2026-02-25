from fastapi import FastAPI
from app.router import router

app = FastAPI(title="Furniture Chatbot")

app.include_router(router)

@app.get("/")
def health():
    return {"status": "Running"}