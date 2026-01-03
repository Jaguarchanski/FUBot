import asyncio
from fastapi import FastAPI, Request
from bot import app as tg_app
from notifier import notify_loop
import uvicorn

API = FastAPI()

@API.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = tg_app.update_queue.update_from_dict(data)
    await tg_app.update_queue.put(update)
    return {"ok": True}

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(notify_loop())
    uvicorn.run(API, host="0.0.0.0", port=8000)
