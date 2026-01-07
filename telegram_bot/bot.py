from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import aiosqlite
from database.db import DB_PATH

# Стан для розмови (чекаємо введення числа)
WAITING_THRESHOLD = 1

async def get_settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("Set Timezone (UTC)", callback_data="set_tz")],
        [InlineKeyboardButton("Set Funding Threshold (%)", callback_data="set_threshold")],
        [InlineKeyboardButton("My Profile 👤", callback_data="my_profile")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please type your desired threshold (e.g., 1.2 or 0.05):")
    return WAITING_THRESHOLD

async def save_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.replace(',', '.')
    try:
        val = float(user_input)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Success! Alert threshold set to **{val}%**", parse_mode="Markdown")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Please enter a value like 1.5 or 0.8:")
        return WAITING_THRESHOLD

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "set_tz":
        tz_keyboard = [
            [InlineKeyboardButton("UTC+0", callback_data="tz_0"), InlineKeyboardButton("UTC+1", callback_data="tz_1")],
            [InlineKeyboardButton("UTC+2 (Kyiv)", callback_data="tz_2"), InlineKeyboardButton("UTC+3", callback_data="tz_3")],
            [InlineKeyboardButton("UTC+5", callback_data="tz_5"), InlineKeyboardButton("UTC+8", callback_data="tz_8")]
        ]
        await query.edit_message_text("Select your Timezone:", reply_markup=InlineKeyboardMarkup(tz_keyboard))
    
    elif query.data.startswith("tz_"):
        tz_val = int(query.data.split("_")[1])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (tz_val, query.from_user.id))
            await db.commit()
        await query.edit_message_text(f"✅ Timezone set to **UTC{tz_val:+}**")

    elif query.data == "my_profile":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan, threshold, timezone FROM users WHERE user_id = ?", (query.from_user.id,)) as c:
                row = await c.fetchone()
                text = (f"👤 **Your Profile**\n\nPlan: {row[0]}\nThreshold: {row[1]}%\nTimezone: UTC{row[2]:+}\n\n"
                        f"Supported Exchanges: 9 (Binance, Bybit, OKX, Gate, Bitget, MEXC, Huobi, KuCoin, dYdX)")
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=await get_settings_keyboard())
