import os, httpx, aiosqlite, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

WAITING_THRESHOLD, WAITING_UTC = 1, 2

async def get_settings_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("Top Fundings 📊", callback_data="show_top")],
        [InlineKeyboardButton("Set Timezone (Manual UTC) 🕒", callback_data="set_tz_manual")],
        [InlineKeyboardButton("Set Threshold (%) 📊", callback_data="set_threshold")],
        [InlineKeyboardButton("My Exchanges 🏦", callback_data="manage_exchanges")],
        [InlineKeyboardButton("Alert Lead Time (Min) 🔔", callback_data="set_lead_time")],
        [InlineKeyboardButton("My Profile 👤", callback_data="my_profile")],
        [InlineKeyboardButton("Upgrade to Premium (50$ USDT) 💎", callback_data="buy_premium")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return [InlineKeyboardButton("« Back to Menu", callback_data="main_menu")]

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "main_menu":
        await query.edit_message_text("⚙️ **Settings Menu**:", reply_markup=await get_settings_keyboard(user_id), parse_mode="Markdown")
    elif data == "show_top":
        await show_top_fundings(query, user_id)
    # ... (інші колбеки залишаються як були)

async def show_top_fundings(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
            u_data = await c.fetchone()
            plan = u_data[0] if u_data else "Free"
            user_utc = u_data[1] if u_data else 0.0
        
        async with db.execute("SELECT exchange, symbol, rate, next_funding_time FROM fundings ORDER BY ABS(rate) DESC LIMIT 15") as c:
            rows = await c.fetchall()

    text = f"📊 **Top Funding Rates ({plan})**\n"
    text += f"🌍 Your Timezone: UTC {user_utc:+}\n\n"

    if not rows:
        text += "Collecting data... please wait."
    else:
        for ex, sym, rate, next_time in rows:
            rate_abs = abs(rate)
            time_str = "N/A"
            if next_time:
                try:
                    dt = datetime.datetime.fromisoformat(next_time.replace('Z', '+00:00'))
                    user_time = dt + datetime.timedelta(hours=user_utc)
                    time_str = user_time.strftime("%H:%M")
                except: pass

            if plan == "Premium":
                text += f"✅ `{sym}` | {ex} | `{rate:.3f}%` | ⏳ {time_str}\n"
            else:
                if ex.lower() == "bybit" and rate_abs <= 1.5:
                    text += f"✅ `{sym}` | {ex} | `{rate:.3f}%` | ⏳ {time_str}\n"
                else:
                    text += f"🔒 `HIDDEN` | {ex} | `{rate:.3f}%` | ⏳ {time_str}\n"
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([back_button()]), parse_mode="Markdown")

# ВІДСУТНІ ФУНКЦІЇ, ЯКІ ВИКЛИКАЛИ ПОМИЛКУ:

async def start_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🔢 Enter your funding threshold in % (e.g. 1.5):")
    return WAITING_THRESHOLD

async def start_utc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🕒 Enter your UTC offset (e.g. 2 for Kyiv, -5 for New York):")
    return WAITING_UTC

async def save_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace(',', '.'))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Threshold set to {val}%", reply_markup=InlineKeyboardMarkup([back_button()]))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return WAITING_THRESHOLD

async def save_utc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace('+', ''))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Timezone set to UTC {val:+}", reply_markup=InlineKeyboardMarkup([back_button()]))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid UTC offset (e.g. 2 or -5.5).")
        return WAITING_UTC
