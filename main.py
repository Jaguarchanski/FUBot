from fastapi import FastAPI, Request
from bot import setup_handlers
from notifier import start_notify_loop
import uvicorn

app = FastAPI()

# Старт бота
setup_handlers()

@app.on_event("startup")
async def startup_event():
    print("🔹 Starting notify loop...")
    await start_notify_loop()

@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
