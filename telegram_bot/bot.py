import os
import httpx
import aiosqlite
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from database.db import DB_PATH

WAITING_THRESHOLD = 1
CRYPTO_PAY_URL = "https://pay.crypt.bot/api/createInvoice"

async def get_settings_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("Set Timezone (UTC)", callback_data="set_tz")],
        [InlineKeyboardButton("Set Threshold (%)", callback_data="set_threshold")],
        [InlineKeyboardButton("Alert Lead Time (Min)", callback_data="set_lead_time")],
        [InlineKeyboardButton("My Profile 👤", callback_data="my_profile")],
        [InlineKeyboardButton("Upgrade to Premium (5$ USDT) 💎", callback_data="buy_premium")]
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
        # Створення рахунку в Crypto Bot
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_BOT_TOKEN")}
        data = {
            "asset": "USDT",
            "amount": "5.00",
            "description": "Premium Subscription - 30 days",
            "paid_btn_name": "openBot",
            "paid_btn_url": f"https://t.me/{(await context.bot.get_me()).username}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(CRYPTO_PAY_URL, headers=headers, json=data)
            res_data = response.json()
            
            if res_data.get("ok"):
                pay_url = res_data["result"]["pay_url"]
                invoice_id = res_data["result"]["invoice_id"]
                
                keyboard = [
                    [InlineKeyboardButton("Pay 5.00 USDT 💸", url=pay_url)],
                    [InlineKeyboardButton("Check Payment ✅", callback_data=f"check_{invoice_id}")],
                    back_button()
                ]
                await query.edit_message_text(
                    "💎 **Upgrade to Premium**\n\nAccess to 9 exchanges, instant alerts, and custom thresholds.\n\nClick the button below to pay via **Crypto Bot**:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("❌ Error creating invoice. Please try later.")

    elif query.data.startswith("check_"):
        invoice_id = query.data.split("_")[1]
        headers = {"Crypto-Pay-API-Token": os.getenv("CRYPTO_BOT_TOKEN")}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://pay.crypt.bot/api/getInvoices?invoice_ids={invoice_id}", headers=headers)
            res_data = response.json()
            
            if res_data.get("ok") and res_data["result"]["items"][0]["status"] == "paid":
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("UPDATE users SET plan = 'Premium' WHERE user_id = ?", (user_id,))
                    await db.commit()
                await query.edit_message_text("🎉 **Payment Successful!** Your Premium plan is now active.", reply_markup=InlineKeyboardMarkup([back_button()]))
            else:
                await query.answer("Payment not detected yet. Try again in a minute.", show_alert=True)

    # ... інші хендлери (tz, lead_time, my_profile) залишаються такими ж, як у попередній відповіді
    elif query.data == "set_tz":
        tz_keyboard = [[InlineKeyboardButton("UTC+0", callback_data="tz_0"), InlineKeyboardButton("UTC+2", callback_data="tz_2")], back_button()]
        await query.edit_message_text("Select Timezone:", reply_markup=InlineKeyboardMarkup(tz_keyboard))

    elif query.data.startswith("tz_"):
        val = int(query.data.split("_")[1])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (val, user_id))
            await db.commit()
        await query.edit_message_text(f"✅ Timezone set to UTC{val:+}", reply_markup=InlineKeyboardMarkup([back_button()]))

    elif query.data == "set_lead_time":
        lt_keyboard = [
            [InlineKeyboardButton("5 min", callback_data="lt_5"), InlineKeyboardButton("15 min", callback_data="lt_15")],
            [InlineKeyboardButton("1 hour", callback_data="lt_60"), InlineKeyboardButton("4 hours", callback_data="lt_240")],
            back_button()
        ]
        await query.edit_message_text("Notify me BEFORE funding:", reply_markup=InlineKeyboardMarkup(lt_keyboard))

    elif query.data.startswith("lt_"):
        val = int(query.data.split("_")[1])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET alert_lead_time = ? WHERE user_id = ?", (val, user_id))
            await db.commit()
        await query.edit_message_text(f"✅ Lead time: {val} min.", reply_markup=InlineKeyboardMarkup([back_button()]))

    elif query.data == "my_profile":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan, threshold, timezone, alert_lead_time FROM users WHERE user_id = ?", (user_id,)) as c:
                row = await c.fetchone()
                exchanges = "Bybit, BingX, Binance, MEXC, KuCoin, Huobi, Gate.io, OKX, Bitget"
                text = (f"👤 **Profile**\n\n**Plan:** {row[0]}\n**Threshold:** {row[1]}%\n"
                        f"**Timezone:** UTC{row[2]:+}\n**Alert:** {row[3]} min before\n\n"
                        f"**Exchanges:** {exchanges}")
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([back_button()]))

async def start_threshold_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("Type threshold (e.g. 1.2):", reply_markup=InlineKeyboardMarkup([back_button()]))
    return WAITING_THRESHOLD

async def save_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.replace(',', '.'))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET threshold = ? WHERE user_id = ?", (val, update.effective_user.id))
            await db.commit()
        await update.message.reply_text(f"✅ Threshold: {val}%", reply_markup=InlineKeyboardMarkup([back_button()]))
        return ConversationHandler.END
    except:
        await update.message.reply_text("Invalid number. Try again:")
        return WAITING_THRESHOLD
