from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from storage import add_user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = await add_user(update.effective_chat.id)
    if user_data["early_bird"]:
        remaining = 500 - sum(1 for u in context.bot_data.get("users", {}).values() if u["early_bird"])
        await update.message.reply_text(
            f"Привіт! Ти отримав безкоштовний тестовий місяць. Залишилось {remaining} місць."
        )
    else:
        await update.message.reply_text("Привіт! Ти на безкоштовному плані.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - почати\n/help - допомога")

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
