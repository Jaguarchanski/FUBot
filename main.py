import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN
from proxy import get_request
from database import create_user, early_left
from notifier import notify_loop


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = create_user(update.effective_user.id)

    if user["early"]:
        text = (
            "🎉 You got FREE early access for 1 month!\n"
            f"⏳ Early bird slots left: {early_left()}"
        )
    else:
        text = "Welcome! Free plan active."

    await update.message.reply_text(text)


async def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .request(get_request())   # ✅ ПРАВИЛЬНО
        .build()
    )

    app.add_handler(CommandHandler("start", start))

    app.bot_data["admin"] = 123456789  # <- твій chat_id для тесту

    asyncio.create_task(notify_loop(app))

    await app.initialize()
    await app.start()
    await app.bot.initialize()
    await app.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
