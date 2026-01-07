import os, aiosqlite, httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

WAITING_THRESHOLD, WAITING_UTC = 1, 2
ALL_EXCHANGES = ["binance", "bybit", "okx", "gateio", "bitget", "bingx", "kucoin", "mexc", "htx"]

async def get_settings_keyboard(user_id, plan="FREE"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 LIVE FUNDINGS", callback_data="show_top")],
        [InlineKeyboardButton("🏛 EXCHANGES", callback_data="manage_exchanges"),
         InlineKeyboardButton("📈 THRESHOLD", callback_data="set_threshold")],
        [InlineKeyboardButton("🔔 ALERT TIME", callback_data="set_alert_time"),
         InlineKeyboardButton("🕒 TIMEZONE", callback_data="set_tz_manual")],
        [InlineKeyboardButton("👤 PROFILE", callback_data="my_profile"),
         InlineKeyboardButton("💎 PREMIUM", callback_data="buy_premium")]
    ])

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan, selected_exchanges, threshold FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
    
    plan, sel_ex, thr = row if row else ("FREE", "bybit", 0.1)

    if query.data == "show_top":
        async with aiosqlite.connect(DB_PATH) as db:
            ex_list = sel_ex.split(',')
            # Тільки ті біржі, що обрав юзер
            placeholders = ','.join(['?'] * len(ex_list))
            async with db.execute(f"SELECT exchange, symbol, rate FROM fundings WHERE exchange IN ({placeholders}) ORDER BY ABS(rate) DESC LIMIT 15", ex_list) as c:
                rows = await c.fetchall()

        txt = "📊 **LIVE FUNDING RATES**\n\n"
        txt += "<code>EX  | SYMBOL  | RATE %</code>\n"
        txt += "<code>-----------------------</code>\n"
        for ex, sym, rate in rows:
            display_sym = sym.split(':')[0].replace('/USDT', '')
            # FREE LOGIC: Blur symbol if rate >= 1.5%
            if plan == "FREE" and abs(rate) >= 1.5:
                display_sym = "******"
            
            emoji = "🟢" if rate > 0 else "🔴"
            txt += f"<code>{ex[:2].upper():<3} | {display_sym:<7} | {rate:>+7.4f}%</code> {emoji}\n"
        
        kb = [[InlineKeyboardButton("🔄 Refresh", callback_data="show_top")], [InlineKeyboardButton("« Back", callback_data="main_menu")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

    elif query.data == "manage_exchanges":
        if plan == "FREE":
            await query.answer("Free Plan is limited to Bybit only.", show_alert=True)
            return
        # Побудова кнопок для 9 бірж
        kb = []
        for i in range(0, len(ALL_EXCHANGES), 2):
            row_btns = []
            for ex in ALL_EXCHANGES[i:i+2]:
                status = "✅" if ex in sel_ex.split(',') else "❌"
                row_btns.append(InlineKeyboardButton(f"{status} {ex.upper()}", callback_data=f"toggle_{ex}"))
            kb.append(row_btns)
        kb.append([InlineKeyboardButton("« Back", callback_data="main_menu")])
        await query.edit_message_text("🏛 **Select Exchanges:**", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("toggle_"):
        ex_to_toggle = query.data.replace("toggle_", "")
        current = sel_ex.split(',')
        if ex_to_toggle in current: current.remove(ex_to_toggle)
        else: current.append(ex_to_toggle)
        new_val = ",".join(filter(None, current))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET selected_exchanges = ? WHERE user_id = ?", (new_val, user_id))
            await db.commit()
        await handle_callbacks(update, context)

    elif query.data == "set_alert_time":
        times = [5, 15, 30, 60, 120, 240]
        kb = []
        for t in times:
            label = f"{t}m" if t < 60 else f"{t//60}h"
            kb.append(InlineKeyboardButton(label, callback_data=f"save_alert_{t}"))
        reply_kb = [kb[i:i+3] for i in range(0, len(kb), 3)]
        reply_kb.append([InlineKeyboardButton("« Back", callback_data="main_menu")])
        await query.edit_message_text("🔔 **Alert timing:**\nChoose how many minutes before settlement:", reply_markup=InlineKeyboardMarkup(reply_kb))

    elif query.data.startswith("save_alert_"):
        m = int(query.data.split('_')[-1])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET alert_time = ? WHERE user_id = ?", (m, user_id))
            await db.commit()
        await query.answer(f"Alerts set to {m} minutes before.")
        await handle_callbacks(update, context)

    elif query.data == "main_menu":
        await query.edit_message_text("⚙️ **Dashboard:**", reply_markup=await get_settings_keyboard(user_id, plan), parse_mode="Markdown")

# Threshold & UTC Conversation handlers English versions
async def start_threshold_input(update, context):
    await update.callback_query.edit_message_text("🔢 **Enter threshold %** (e.g. 0.1):")
    return WAITING_THRESHOLD

async def save_threshold(update, context):
    try:
        val = float(update.message.text.replace(',', '.'))
        # FREE limit
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan FROM users WHERE user_id = ?", (update.effective_user.id,)) as c:
                plan = (await c.fetchone())[0]
            if plan == "FREE" and val > 1.5:
                await update.message.reply_text("❌ Max threshold for Free Plan is 1.5%. Upgrade to Premium!")
                return ConversationHandler.END
            await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Threshold set to {val}%", reply_markup=await get_settings_keyboard(update.effective_user.id, plan))
    except: pass
    return ConversationHandler.END

# UTC manual input similarly...
async def start_utc_input(update, context):
    await update.callback_query.edit_message_text("🕒 **Enter UTC offset** (e.g. 2 for Kyiv):")
    return WAITING_UTC

async def save_utc(update, context):
    try:
        val = float(update.message.text)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Timezone set to UTC{val:+}")
    except: pass
    return ConversationHandler.END
