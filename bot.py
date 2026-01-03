from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from storage import add_user, update_threshold

app = ApplicationBuilder().token("YOUR_TOKEN_HERE").build()
bot = app.bot

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    await update.message.reply_text(
        "Привіт! Твій funding alert бот активований. Можеш змінити поріг /threshold <value>."
    )

async def threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        await update.message.reply_text("Використання: /threshold <value>")
        return
    try:
        value = float(context.args[0])
        update_threshold(chat_id, value)
        await update.message.reply_text(f"Поріг funding оновлено на {value}%")
    except ValueError:
        await update.message.reply_text("Введіть правильне число")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("threshold", threshold))
