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

async def show_top_fundings(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        # Отримуємо план та UTC користувача
        async with db.execute("SELECT plan, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
            u_data = await c.fetchone()
            plan = u_data[0] if u_data else "Free"
            user_utc = u_data[1] if u_data else 0.0
        
        # Отримуємо топ ставок
        async with db.execute("SELECT exchange, symbol, rate, next_funding_time FROM fundings ORDER BY ABS(rate) DESC LIMIT 15") as c:
            rows = await c.fetchall()

    text = f"📊 **Top Funding Rates ({plan})**\n"
    text += f"🌍 Your Timezone: UTC {user_utc:+}\n\n"

    if not rows:
        text += "Collecting data... please wait."
    else:
        for ex, sym, rate, next_time in rows:
            rate_abs = abs(rate)
            
            # Обчислення часу фандингу для юзера
            time_str = "N/A"
            if next_time:
                try:
                    # Час у БД зазвичай в UTC
                    dt = datetime.datetime.fromisoformat(next_time.replace('Z', '+00:00'))
                    user_time = dt + datetime.timedelta(hours=user_utc)
                    time_str = user_time.strftime("%H:%M")
                except: pass

            # Логіка відображення
            if plan == "Premium":
                text += f"✅ `{sym}` | {ex} | `{rate:.3f}%` | ⏳ {time_str}\n"
            else:
                # FREE ПЛАН
                if ex.lower() == "bybit" and rate_abs <= 1.5:
                    text += f"✅ `{sym}` | {ex} | `{rate:.3f}%` | ⏳ {time_str}\n"
                else:
                    # Тизер для всіх інших випадків
                    text += f"🔒 `HIDDEN` | {ex} | `{rate:.3f}%` | ⏳ {time_str}\n"
    
    if plan == "Free":
        text += "\n⭐ _Premium: Unlock all exchanges & hidden coins!_"

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([back_button()]), parse_mode="Markdown")

# --- Решта функцій (handle_callbacks, save_utc тощо) залишаються як у попередніх версіях ---
# Переконайся, що додано CallbackQueryHandler для "show_top"
