import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import db_load, db_save
from config import BOT_TOKEN, PROXY_URL, FREE_MAX_FUNDING, DEFAULT_FREE_EXCHANGE, ALL_EXCHANGES, EARLY_BIRD_DURATION_DAYS
from i18n import MESSAGES
from funding_sources import FUNDING_DATA
from proxy import get_proxy
from datetime import datetime, timedelta

data = db_load()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in data["users"]:
        if data["early_bird_remaining"] > 0:
            data["users"][user_id] = {
                "plan": "early_bird",
                "expiry": (datetime.utcnow() + timedelta(days=EARLY_BIRD_DURATION_DAYS)).isoformat()
            }
            data["early_bird_remaining"] -= 1
            msg = MESSAGES["welcome_early_bird"].format(remaining=data["early_bird_remaining"])
        else:
            data["users"][user_id] = {"plan": "free", "expiry": None}
            msg = MESSAGES["welcome_free"]
        db_save(data)
    else:
        plan = data["users"][user_id]["plan"]
        if plan == "free":
            msg = MESSAGES["welcome_free"]
        else:
            msg = MESSAGES["welcome_early_bird"].format(remaining=data["early_bird_remaining"])
    await update.message.reply_text(msg)

async def top_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = data["users"].get(user_id)
    if not user:
        await update.message.reply_text("Спочатку натисни /start")
        return

    plan = user["plan"]
    msg_lines = []

    exchanges = ALL_EXCHANGES if plan != "free" else [DEFAULT_FREE_EXCHANGE]

    for ex in exchanges:
        for f in FUNDING_DATA.get(ex, []):
            rate = f["funding_rate"]
            if plan == "free" and rate > FREE_MAX_FUNDING:
                msg_lines.append(f"{f['time']} - {ex} - [hidden coin]")
            else:
                msg_lines.append(f"{f['time']} - {ex} - {f['pair']} - {rate}%")
    msg = "\n".join(msg_lines) if msg_lines else "Немає фандингів за обраними параметрами."
    await update.message.reply_text(msg)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).proxy_url(get_proxy()).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top", top_funding))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
