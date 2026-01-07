import os, httpx, aiosqlite
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

    elif data == "buy_premium":
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_BOT_TOKEN")}
        payload = {"asset": "USDT", "amount": "50.00", "description": "Premium 30 Days"}
        async with httpx.AsyncClient() as client:
            res = await client.post("https://pay.crypt.bot/api/createInvoice", headers=headers, json=payload)
            r = res.json()
            if r.get("ok"):
                url = r["result"]["pay_url"]
                inv_id = r["result"]["invoice_id"]
                kb = [[InlineKeyboardButton("Pay 50.00 USDT 💸", url=url)], [InlineKeyboardButton("Check Payment ✅", callback_data=f"check_{inv_id}")], back_button()]
                await query.edit_message_text("💎 **Premium Access**\nUnlock all coins and 9 exchanges.", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("check_"):
        inv_id = data.split("_")[1]
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_BOT_TOKEN")}
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://pay.crypt.bot/api/getInvoices?invoice_ids={inv_id}", headers=headers)
            r = res.json()
            if r.get("ok") and r["result"]["items"][0]["status"] == "paid":
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("UPDATE users SET plan = 'Premium' WHERE user_id = ?", (user_id,))
                    await db.commit()
                await query.edit_message_text("🎉 Welcome to Premium!", reply_markup=InlineKeyboardMarkup([back_button()]))
            else:
                await query.answer("Payment not detected yet.", show_alert=True)

    elif data == "manage_exchanges":
        await show_exchanges_menu(query, user_id)

    elif data.startswith("toggle_"):
        ex = data.replace("toggle_", "")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE user_exchanges SET is_enabled = 1 - is_enabled WHERE user_id = ? AND exchange_name = ?", (user_id, ex))
            await db.commit()
        await show_exchanges_menu(query, user_id)

    elif data == "set_tz_manual":
        await query.edit_message_text("Type your UTC offset (e.g. 2 or -5):")
        return WAITING_UTC

async def show_top_fundings(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as c:
            plan = (await c.fetchone())[0]
        async with db.execute("SELECT exchange, symbol, rate FROM fundings ORDER BY ABS(rate) DESC LIMIT 15") as c:
            rows = await c.fetchall()

    text = "📊 **Top Funding Rates**\n\n"
    for ex, sym, rate in rows:
        if plan == "Premium" or abs(rate) <= 1.5:
            text += f"✅ `{sym}` | {ex} | `{rate:.3f}%` \n"
        else:
            text += f"🔒 `HIDDEN` | {ex} | `{rate:.3f}%` \n"
    
    if plan == "Free": text += "\n⭐ _Get Premium to see hidden coins (rate > 1.5%)_"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([back_button()]), parse_mode="Markdown")

async def show_exchanges_menu(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT exchange_name, is_enabled FROM user_exchanges WHERE user_id = ?", (user_id,)) as c:
            rows = await c.fetchall()
    kb = [[InlineKeyboardButton(f"{'✅' if r[1] else '❌'} {r[0]}", callback_data=f"toggle_{r[0]}")] for r in rows]
    kb.append(back_button())
    await query.edit_message_text("🏦 **Manage Exchanges**", reply_markup=InlineKeyboardMarkup(kb))

async def start_threshold_input(q, c): await q.callback_query.edit_message_text("Enter threshold %:"); return WAITING_THRESHOLD
async def start_utc_input(q, c): await q.callback_query.edit_message_text("Enter UTC offset:"); return WAITING_UTC
async def save_threshold(u, c):
    val = float(u.message.text.replace(',','.'))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, u.effective_user.id))
        await db.commit()
    await u.message.reply_text(f"✅ Set to {val}%", reply_markup=InlineKeyboardMarkup([back_button()]))
    return ConversationHandler.END
async def save_utc(u, c):
    val = float(u.message.text.replace('+',''))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, u.effective_user.id))
        await db.commit()
    await u.message.reply_text(f"✅ UTC {val:+} set", reply_markup=InlineKeyboardMarkup([back_button()]))
    return ConversationHandler.END
