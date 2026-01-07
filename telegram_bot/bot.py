import os
import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

# Константи станів для ConversationHandler
WAITING_THRESHOLD, WAITING_UTC = 1, 2
ALL_EXCHANGES = ["binance", "bybit", "okx", "gateio", "bitget", "bingx", "kucoin", "mexc", "htx"]

# --- КЛАВІАТУРИ ---

async def get_settings_keyboard(user_id, plan="FREE"):
    """Головне меню"""
    kb = [
        [InlineKeyboardButton("📊 LIVE FUNDINGS", callback_data="show_top")],
        [InlineKeyboardButton("🏛 EXCHANGES", callback_data="manage_exchanges"),
         InlineKeyboardButton("📈 THRESHOLD", callback_data="set_threshold")],
        [InlineKeyboardButton("🔔 ALERT TIME", callback_data="set_alert_time"),
         InlineKeyboardButton("🕒 TIMEZONE", callback_data="set_tz_manual")],
        [InlineKeyboardButton("👤 PROFILE", callback_data="my_profile")]
    ]
    return InlineKeyboardMarkup(kb)

def back_to_menu_kb():
    """Універсальна кнопка Назад"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("« Назад до меню", callback_data="main_menu")]])

# --- ОБРОБКА CALLBACKS (КНОПОК) ---

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Завжди відповідаємо на запит, щоб прибрати "годинник" на кнопці
    try:
        await query.answer()
    except:
        pass

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan, selected_exchanges, threshold, timezone FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
    
    plan, sel_ex, thr, tz = row if row else ("FREE", "bybit", 0.1, 0.0)

    # 1. ГОЛОВНЕ МЕНЮ
    if query.data == "main_menu":
        await query.edit_message_text(
            "⚙️ **Панель керування:**",
            reply_markup=await get_settings_keyboard(user_id, plan),
            parse_mode="Markdown"
        )

    # 2. ПОКАЗ ФАНДИНГУ
    elif query.data == "show_top":
        async with aiosqlite.connect(DB_PATH) as db:
            ex_list = sel_ex.split(',')
            placeholders = ','.join(['?'] * len(ex_list))
            async with db.execute(f"SELECT exchange, symbol, rate FROM fundings WHERE exchange IN ({placeholders}) ORDER BY ABS(rate) DESC LIMIT 15", ex_list) as c:
                rows = await c.fetchall()

        txt = "📊 **ТОП ФАНДИНГ (LIVE)**\n\n"
        txt += "<code>EX  | SYMBOL  | RATE %</code>\n"
        txt += "<code>-----------------------</code>\n"
        
        if not rows:
            txt += "Дані ще збираються, зачекайте хвилину..."
        else:
            for ex, sym, rate in rows:
                display_sym = sym.split(':')[0].replace('/USDT', '')
                if plan == "FREE" and abs(rate) >= 1.5:
                    display_sym = "******"
                emoji = "🟢" if rate > 0 else "🔴"
                txt += f"<code>{ex[:2].upper():<3} | {display_sym:<7} | {rate:>+7.4f}%</code> {emoji}\n"
        
        kb = [[InlineKeyboardButton("🔄 Оновити", callback_data="show_top")], [InlineKeyboardButton("« Назад", callback_data="main_menu")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

    # 3. КЕРУВАННЯ БІРЖАМИ
    elif query.data == "manage_exchanges" or query.data.startswith("toggle_"):
        if plan == "FREE":
            await query.answer("На FREE плані доступна тільки Bybit", show_alert=True)
            return

        if query.data.startswith("toggle_"):
            ex_to_toggle = query.data.replace("toggle_", "")
            current = sel_ex.split(',')
            if ex_to_toggle in current: current.remove(ex_to_toggle)
            else: current.append(ex_to_toggle)
            sel_ex = ",".join(filter(None, current))
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET selected_exchanges = ? WHERE user_id = ?", (sel_ex, user_id))
                await db.commit()

        kb = []
        for i in range(0, len(ALL_EXCHANGES), 2):
            row_btns = []
            for ex in ALL_EXCHANGES[i:i+2]:
                status = "✅" if ex in sel_ex.split(',') else "❌"
                row_btns.append(InlineKeyboardButton(f"{status} {ex.upper()}", callback_data=f"toggle_{ex}"))
            kb.append(row_btns)
        kb.append([InlineKeyboardButton("« Назад", callback_data="main_menu")])
        
        # Використовуємо try/except щоб уникнути помилки "Message is not modified"
        try:
            await query.edit_message_text("🏛 **Виберіть біржі для моніторингу:**", reply_markup=InlineKeyboardMarkup(kb))
        except:
            pass

    # 4. ПРОФІЛЬ
    elif query.data == "my_profile":
        txt = (f"👤 **Ваш профіль:**\n\n"
               f"ID: `{user_id}`\n"
               f"План: **{plan}**\n"
               f"Поріг: `{thr}%` (Threshold)\n"
               f"Пояс: `UTC{tz:+}`\n"
               f"Біржі: `{sel_ex.upper()}`")
        await query.edit_message_text(txt, reply_markup=back_to_menu_kb(), parse_mode="Markdown")

# --- CONVERSATION LOGIC (TEXT INPUT) ---

async def start_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📈 **Введіть поріг спрацювання алерту (число)**\nНаприклад: `0.1` або `1.5`",
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown"
    )
    return WAITING_THRESHOLD

async def save_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        val = float(update.message.text.replace(',', '.'))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, user_id))
            await db.commit()
        await update.message.reply_text(f"✅ Поріг встановлено: {val}%", reply_markup=back_to_menu_kb())
    except ValueError:
        await update.message.reply_text("❌ Помилка! Введіть число (наприклад 0.1)", reply_markup=back_to_menu_kb())
    return ConversationHandler.END

async def start_utc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🕒 **Введіть зміщення часового поясу (UTC)**\nНаприклад: `2` для Києва або `-5` для Нью-Йорка.",
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown"
    )
    return WAITING_UTC

async def save_utc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        val = float(update.message.text)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, user_id))
            await db.commit()
        await update.message.reply_text(f"✅ Часовий пояс встановлено: UTC{val:+}", reply_markup=back_to_menu_kb())
    except ValueError:
        await update.message.reply_text("❌ Введіть ціле число або десятковий дріб.", reply_markup=back_to_menu_kb())
    return ConversationHandler.END
