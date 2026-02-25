from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Furniture chatbot running"}

@app.post("/chat")
def chat():
    return {"message": "Chat endpoint working"}
