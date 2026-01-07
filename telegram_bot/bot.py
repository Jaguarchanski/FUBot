import os, httpx, aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

WAITING_THRESHOLD, WAITING_UTC = 1, 2

async def get_settings_keyboard(user_id):
    keyboard = [
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
    await query.answer()
    user_id = query.from_user.id

    if query.data == "main_menu":
        await query.edit_message_text("⚙️ **Settings Menu**:", reply_markup=await get_settings_keyboard(user_id), parse_mode="Markdown")

    elif query.data == "buy_premium":
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_BOT_TOKEN")}
        data = {"asset": "USDT", "amount": "50.00", "description": "Premium 30 Days", "paid_btn_name": "openBot", "paid_btn_url": f"https://t.me/{(await context.bot.get_me()).username}"}
        async with httpx.AsyncClient() as client:
            res = await client.post("https://pay.crypt.bot/api/createInvoice", headers=headers, json=data)
            res_data = res.json()
            if res_data.get("ok"):
                pay_url = res_data["result"]["pay_url"]
                invoice_id = res_data["result"]["invoice_id"]
                kb = [[InlineKeyboardButton("Pay 50.00 USDT 💸", url=pay_url)], [InlineKeyboardButton("Check Payment ✅", callback_data=f"check_{invoice_id}")], back_button()]
                await query.edit_message_text("💎 **Upgrade to Premium**\nPrice: 50 USDT", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("check_"):
        invoice_id = query.data.split("_")[1]
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_BOT_TOKEN")}
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}", headers=headers)
            res_data = res.json()
            if res_data.get("ok") and res_data["result"]["items"][0]["status"] == "paid":
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("UPDATE users SET plan = 'Premium' WHERE user_id = ?", (user_id,))
                    await db.commit()
                await query.edit_message_text("🎉 Payment Successful!", reply_markup=InlineKeyboardMarkup([back_button()]))
            else:
                await query.answer("Not paid yet.", show_alert=True)

    elif query.data == "manage_exchanges":
        await show_exchanges_menu(query, user_id)

    elif query.data.startswith("toggle_"):
        ex_name = query.data.replace("toggle_", "")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE user_exchanges SET is_enabled = 1 - is_enabled WHERE user_id = ? AND exchange_name = ?", (user_id, ex_name))
            await db.commit()
        await show_exchanges_menu(query, user_id)

    elif query.data == "set_tz_manual":
        await query.edit_message_text("Enter your UTC offset (e.g., `2` or `-5`):", parse_mode="Markdown")
        return WAITING_UTC

    elif query.data == "set_lead_time":
        lt_kb = [[InlineKeyboardButton("5m", callback_data="lt_5"), InlineKeyboardButton("15m", callback_data="lt_15")], [InlineKeyboardButton("1h", callback_data="lt_60"), InlineKeyboardButton("4h", callback_data="lt_240")], back_button()]
        await query.edit_message_text("Notify me before funding:", reply_markup=InlineKeyboardMarkup(lt_kb))

    elif query.data.startswith("lt_"):
        val = int(query.data.split("_")[1])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET alert_lead_time = ? WHERE user_id = ?", (val, user_id))
            await db.commit()
        await query.edit_message_text(f"✅ Set to {val} min.", reply_markup=InlineKeyboardMarkup([back_button()]))

    elif query.data == "my_profile":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan, threshold, timezone, alert_lead_time FROM users WHERE user_id = ?", (user_id,)) as c:
                r = await c.fetchone()
            async with db.execute("SELECT exchange_name FROM user_exchanges WHERE user_id = ? AND is_enabled = 1", (user_id,)) as c:
                exs = ", ".join([x[0] for x in await c.fetchall()])
        await query.edit_message_text(f"👤 **Profile**\nPlan: {r[0]}\nThreshold: {r[1]}%\nUTC: {r[2]:+}\nLead: {r[3]}m\n\n**Active:** {exs}", reply_markup=InlineKeyboardMarkup([back_button()]), parse_mode="Markdown")

async def show_exchanges_menu(query, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT exchange_name, is_enabled FROM user_exchanges WHERE user_id = ?", (user_id,)) as c:
            rows = await c.fetchall()
    kb = [[InlineKeyboardButton(f"{'✅' if r[1] else '❌'} {r[0]}", callback_data=f"toggle_{r[0]}")] for r in rows]
    kb.append(back_button())
    await query.edit_message_text("🏦 **Select Exchanges:**", reply_markup=InlineKeyboardMarkup(kb))

async def start_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("Type threshold (e.g. 1.5):")
    return WAITING_THRESHOLD

async def start_utc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("Enter UTC (e.g. 2):")
    return WAITING_UTC

async def save_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = float(update.message.text.replace(',', '.'))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, update.effective_user.id))
        await db.commit()
    await update.message.reply_text(f"✅ Threshold: {val}%", reply_markup=InlineKeyboardMarkup([back_button()]))
    return ConversationHandler.END

async def save_utc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = float(update.message.text.replace('+', ''))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, update.effective_user.id))
        await db.commit()
    await update.message.reply_text(f"✅ UTC: {val:+}", reply_markup=InlineKeyboardMarkup([back_button()]))
    return ConversationHandler.END
