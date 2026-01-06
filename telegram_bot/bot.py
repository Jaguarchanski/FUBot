from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes
import database.db as db_module
import aiosqlite

DB_PATH = "furate.db"

# Головне меню (кнопки під повідомленням)
def get_main_menu_keyboard(is_premium: bool):
    keyboard = [
        [InlineKeyboardButton("📊 My Status", callback_data='status'),
         InlineKeyboardButton("📈 List Rates", callback_data='list_rates')],
        [InlineKeyboardButton("⚙️ Settings", callback_data='settings_menu')],
        [InlineKeyboardButton("🏦 Exchanges", callback_data='exchanges_menu')]
    ]
    if not is_premium:
        keyboard.append([InlineKeyboardButton("💎 Upgrade to Premium", callback_data='upgrade')])
    
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Перевіряємо, чи є користувач у базі
        async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            
        if user is None:
            # Новий користувач: перевіряємо лічильник Early Bird
            slots_left = await db_module.get_promo_slots()
            
            if slots_left > 0:
                plan = 'premium' # Надаємо статус Early Bird
                await db_module.decrease_promo_slots()
                welcome_text = (
                    f"🎁 **Congratulations!**\n"
                    f"You secured one of the 500 free slots.\n"
                    f"You have **1 month of FREE Premium** access!"
                )
            else:
                plan = 'free'
                welcome_text = "Welcome to **FURate**! Start monitoring funding rates now."

            await db.execute(
                "INSERT INTO users (user_id, plan) VALUES (?, ?)", 
                (user_id, plan)
            )
            await db.commit()
        else:
            plan = user[0]
            welcome_text = "Welcome back to **FURate**!"

    slots_now = await db_module.get_promo_slots()
    
    final_text = (
        f"✨ {welcome_text}\n\n"
        f"🔥 **Early Bird Slots: {slots_now}/500 remaining**\n\n"
        f"Use the menu below to configure your alerts."
    )
    
    await update.message.reply_text(
        final_text,
        reply_markup=get_main_menu_keyboard(plan != 'free'),
        parse_mode=constants.ParseMode.MARKDOWN
    )

# Обробка натискань на кнопки (CallbackQuery)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'status':
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan, threshold, timezone, alert_lead_time FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    plan, thr, tz, alt = row
                    status_text = (
                        f"📊 **Your Subscription Status**\n\n"
                        f"🔹 **Plan:** `{plan.upper()}`\n"
                        f"🔹 **Threshold:** `{thr}%`\n"
                        f"🔹 **Timezone:** `{tz}`\n"
                        f"🔹 **Alert Time:** `{alt} min before funding`"
                    )
                    await query.edit_message_text(status_text, reply_markup=get_main_menu_keyboard(plan != 'free'), parse_mode=constants.ParseMode.MARKDOWN)

    elif query.data == 'settings_menu':
        # Тут буде логіка підменю налаштувань (TZ, Threshold тощо)
        await query.edit_message_text("⚙️ **Settings Menu**\nChoose what to change:", 
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🕒 Timezone", callback_data='set_tz'),
                 InlineKeyboardButton("🎯 Threshold", callback_data='set_thr')],
                [InlineKeyboardButton("⏳ Alert Time", callback_data='set_alert')],
                [InlineKeyboardButton("⬅️ Back", callback_data='main_menu')]
            ]), parse_mode=constants.ParseMode.MARKDOWN)

    elif query.data == 'main_menu':
        # Повернення в головне меню (потрібно перевірити план)
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT plan FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                plan = row[0] if row else 'free'
                await query.edit_message_text("Main Menu:", reply_markup=get_main_menu_keyboard(plan != 'free'))
