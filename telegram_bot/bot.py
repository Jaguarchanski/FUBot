import os, aiosqlite, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

WAITING_THRESHOLD, WAITING_UTC = 1, 2

def parse_date(date_str):
    if not date_str or date_str == "None": return None
    try:
        return datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        try:
            ts = float(date_str)
            if ts > 1e11: ts /= 1000
            return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        except: return None

async def get_settings_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("Top Fundings 📊", callback_data="show_top")],
        [InlineKeyboardButton("Filter Exchanges 🏛", callback_data="manage_exchanges")],
        [InlineKeyboardButton("Set Threshold (%) 📉", callback_data="set_threshold")],
        [InlineKeyboardButton("Timezone (UTC) 🕒", callback_data="set_tz_manual")],
        [InlineKeyboardButton("My Profile 👤", callback_data="my_profile"), 
         InlineKeyboardButton("Premium 💎", callback_data="buy_premium")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "main_menu":
        await query.edit_message_text("⚙️ **Settings Menu**:", reply_markup=await get_settings_keyboard(user_id), parse_mode="Markdown")
    
    elif query.data == "show_top":
        await show_top_fundings(query, user_id)

    elif query.data == "manage_exchanges":
        await query.edit_message_text("🏛 **Exchanges Filter**\n\n_Choose which exchanges to track (Premium function)._", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="main_menu")]]))
        
    elif query.data == "my_profile":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan, expiry_date, threshold, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
                row = await c.fetchone()
        
        plan, expiry, thr, utc = row if row else ("Free", None, 1.0, 0.0)
        exp_info = f"\nExpires: `{expiry[:10]}`" if expiry else ""
        text = f"👤 **Profile**\n\nPlan: **{plan}**{exp_info}\nThreshold: `{thr}%`\nTimezone: `UTC {utc:+}`"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="main_menu")]]), parse_mode="Markdown")

    elif query.data == "buy_premium":
        kb = [
            [InlineKeyboardButton("Pay with CryptoBot 💳", url="https://t.me/CryptoBot?start=pay")],
            [InlineKeyboardButton("« Back", callback_data="main_menu")]
        ]
        await query.edit_message_text("💎 **Premium Subscription**\n\n• Unlock all 15+ exchanges\n• See high-rate hidden coins\n• Early Bird: First 500 get 1 month FREE!\n\nPrice: **10 USDT / month**", 
                                      reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def show_top_fundings(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
            u_data = await c.fetchone()
            plan, user_utc = (u_data[0], u_data[1]) if u_data else ("Free", 0.0)
        
        async with db.execute("SELECT exchange, symbol, rate, next_funding_time FROM fundings ORDER BY ABS(rate) DESC LIMIT 15") as c:
            rows = await c.fetchall()

    text = f"📊 Top Fundings ({plan})\n`Ex | Symbol  | Rate   | Time`\n"
    text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    if not rows:
        text += "No data..."
    else:
        for ex, sym, rate, next_time in rows:
            dt = parse_date(next_time)
            time_display = (dt + datetime.timedelta(hours=user_utc)).strftime("%H:%M") if dt else "--:--"
            
            # Логіка приховування для Free
            is_hidden = plan == "Free" and abs(rate) > 0.01 # Наприклад, Free бачить лише дуже низькі ставки
            coin_name = "HIDDEN" if is_hidden else sym[:7]
            
            text += f"`{ex[:2].upper()} | {coin_name:<7} | {rate:+.3f}% | {time_display}`\n"
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="main_menu")]]), parse_mode="Markdown")

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
        await update.message.reply_text(f"✅ Threshold saved: {val}%", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="main_menu")]]))
        return ConversationHandler.END
    except: return WAITING_THRESHOLD

async def save_utc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace('+', ''))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Timezone saved: UTC {val:+}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="main_menu")]]))
        return ConversationHandler.END
    except: return WAITING_UTC
