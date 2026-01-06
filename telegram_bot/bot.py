import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import get_db
from services.funding_service import get_top_funding_rates

logger = logging.getLogger(__name__)

def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Binance", callback_data="ex_binance"),
            InlineKeyboardButton("Bybit", callback_data="ex_bybit"),
            InlineKeyboardButton("OKX", callback_data="ex_okx")
        ],
        [
            InlineKeyboardButton("Bitget", callback_data="ex_bitget"),
            InlineKeyboardButton("Gate.io", callback_data="ex_gateio"),
            InlineKeyboardButton("KuCoin", callback_data="ex_kucoin")
        ],
        [
            InlineKeyboardButton("MEXC", callback_data="ex_mexc"),
            InlineKeyboardButton("HTX", callback_data="ex_htx"),
            InlineKeyboardButton("BingX", callback_data="ex_bingx")
        ],
        [InlineKeyboardButton("📊 My Profile", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        db = await get_db()
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        await db.close()

        welcome_text = (
            "🚀 **Funding Rates Monitor**\n\n"
            "Select an exchange below to get the top funding rates in real-time:"
        )
        await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Start error: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_main")]])
    
    if data.startswith("ex_"):
        exchange_id = data.replace("ex_", "")
        await query.edit_message_text(text=f"🔄 Fetching data from {exchange_id.upper()} using proxy...")
        
        report = await get_top_funding_rates(exchange_id)
        
        await query.edit_message_text(text=report, reply_markup=back_btn, parse_mode="Markdown")

    elif data == "back_to_main":
        await query.edit_message_text(text="Choose an exchange to monitor:", reply_markup=get_main_keyboard())
        
    elif data == "profile":
        await query.edit_message_text(
            text=f"👤 **Profile**\n\nUser ID: `{update.effective_user.id}`\nPlan: `Free`", 
            reply_markup=back_btn, 
            parse_mode="Markdown"
        )
