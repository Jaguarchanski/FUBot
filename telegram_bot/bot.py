import os, aiosqlite, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

WAITING_THRESHOLD, WAITING_UTC = 1, 2

def parse_date(date_str):
    """Універсальний парсер для ISO та Timestamp форматів"""
    if not date_str or date_str == "None": return None
    try:
        return datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        try:
            ts = float(date_str)
            if ts > 1e11: ts /= 1000 # конвертація з мілісекунд у секунди
            return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        except: return None

async def get_settings_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Top Fundings 📊", callback_data="show_top")],
        [InlineKeyboardButton("Set Timezone (UTC) 🕒", callback_data="set_tz_manual")],
        [InlineKeyboardButton("Set Threshold (%) 📊", callback_data="set_threshold")],
        [InlineKeyboardButton("My Profile 👤", callback_data="my_profile")],
        [InlineKeyboardButton("Upgrade to Premium 💎", callback_data="buy_premium")]
    ])

def back_button():
    return InlineKeyboardButton("« Back to Menu", callback_data="main_menu")

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "main_menu":
        await query.edit_message_text("⚙️ **Settings Menu**:", reply_markup=await get_settings_keyboard(user_id), parse_mode="Markdown")
    
    elif query.data == "show_top":
        await show_top_fundings(query, user_id)
        
    elif query.data == "my_profile":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan, threshold, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
                row = await c.fetchone()
        plan, threshold, utc = (row[0], row[1], row[2]) if row else ("Free", 1.0, 0.0)
        text = f"👤 **Your Profile**\n\nPlan: **{plan}**\nThreshold: `{threshold}%`\nTimezone: `UTC {utc:+}`"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button()]]), parse_mode="Markdown")

    elif query.data == "buy_premium":
        await query.edit_message_text("💎 **Premium Subscription**\n\nPrice: 50 USDT\n• All exchanges unlocked\n• High-rate coins visible\n• Real-time alerts\n\n_Contact @admin to upgrade_", 
                                      reply_markup=InlineKeyboardMarkup([[back_button()]]))

async def show_top_fundings(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
            u_data = await c.fetchone()
            plan, user_utc = (u_data[0], u_data[1]) if u_data else ("Free", 0.0)
        
        async with db.execute("SELECT exchange, symbol, rate, next_funding_time FROM fundings ORDER BY ABS(rate) DESC LIMIT 15") as c:
            rows = await c.fetchall()

    text = f"📊 Top Fundings ({plan}) | UTC {user_utc:+}\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"

    if not rows:
        text += "Collecting data... please wait."
    else:
        for ex, sym, rate, next_time in rows:
            dt = parse_date(next_time)
            time_display = (dt + datetime.timedelta(hours=user_utc)).strftime("%H:%M") if dt else "--:--"
            
            # Логіка HIDDEN/VISIBLE
            if plan == "Premium" or (ex.lower() == "bybit" and abs(rate) <= 1.5):
                line = f"{ex[:2].upper()} | {sym[:7]:<7} | {rate:+.3f}% | {time_display}"
            else:
                line = f"{ex[:2].upper()} | HIDDEN  | {rate:+.3f}% | {time_display}"
            text += f"`{line}`\n"
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[back_button()]]), parse_mode="Markdown")

# Функції діалогу для введення даних (UTC та Threshold)
async def start_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🔢 Enter threshold % (e.g. 1.5):")
    return WAITING_THRESHOLD

async def start_utc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🕒 Enter your UTC offset (e.g. 2):")
    return WAITING_UTC

async def save_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace(',', '.'))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Threshold: {val}%", reply_markup=InlineKeyboardMarkup([[back_button()]]))
        return ConversationHandler.END
    except: return WAITING_THRESHOLD

async def save_utc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace('+', ''))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Timezone: UTC {val:+}", reply_markup=InlineKeyboardMarkup([[back_button()]]))
        return ConversationHandler.END
    except: return WAITING_UTC
