import os
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Імпорт ваших сервісів (переконайтеся, що шляхи вірні)
from services.funding_service import get_funding_rates, get_all_exchanges
from database.db_manager import init_db

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Константи
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID") # Ваш ID для сповіщень
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook" if os.getenv('RENDER_EXTERNAL_HOSTNAME') else None

app = FastAPI()
tg_application = None

# --- ЛОГІКА СКАНЕРА ---

async def scan_market_task(context: ContextTypes.DEFAULT_TYPE):
    """Фонове завдання, яке перевіряє всі біржі на аномальний фандинг"""
    threshold = 0.03  # Поріг сповіщення: 0.03% або -0.03%
    exchanges = ["binance", "bybit", "mexc", "bitget", "kucoin", "bingx", "gateio"]
    
    logger.info("🔍 Початок фонового сканування ринку...")
    found_anomalies = []

    for ex_id in exchanges:
        try:
            rates = await get_funding_rates(ex_id)
            if not rates:
                continue
                
            for symbol, rate in rates.items():
                if abs(rate) >= threshold:
                    found_anomalies.append({
                        "ex": ex_id.upper(),
                        "sym": symbol,
                        "rate": rate
                    })
        except Exception as e:
            logger.error(f"Помилка при скануванні {ex_id}: {e}")

    if found_anomalies and ADMIN_ID:
        # Сортуємо за модулем ставки (найвищі зверху)
        found_anomalies.sort(key=lambda x: abs(x['rate']), reverse=True)
        
        message = "🚨 **АНОМАЛЬНИЙ ФАНДИНГ ВИЯВЛЕНО** 🚨\n\n"
        for item in found_anomalies[:15]: # Обмежуємо топ-15, щоб повідомлення не було завеликим
            emoji = "🟢" if item['rate'] > 0 else "🔴"
            message += f"{emoji} `{item['ex']}`: {item['sym']} — `{item['rate']:.4f}%` \n"
        
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode="Markdown")
            logger.info("✅ Сповіщення про аномалії надіслано адміну.")
        except Exception as e:
            logger.error(f"Не вдалося надіслати сповіщення: {e}")

# --- ОБРОБНИКИ ТЕЛЕГРАМ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Binance", callback_data='funding_binance'),
         InlineKeyboardButton("Bybit", callback_data='funding_bybit')],
        [InlineKeyboardButton("MEXC", callback_data='funding_mexc'),
         InlineKeyboardButton("Bitget", callback_data='funding_bitget')],
        [InlineKeyboardButton("KuCoin", callback_data='funding_kucoin'),
         InlineKeyboardButton("BingX", callback_data='funding_bingx')],
        [InlineKeyboardButton("Gate.io", callback_data='funding_gateio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть біржу для перевірки ставок фінансування:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('funding_'):
        ex_id = query.data.split('_')[1]
        await query.edit_message_text(f"⏳ Отримую дані з {ex_id.upper()}...")
        
        rates = await get_funding_rates(ex_id)
        if not rates:
            await query.edit_message_text(f"❌ Не вдалося отримати дані з {ex_id.upper()}. Спробуйте пізніше.")
            return

        # Сортування: найбільші ставки зверху
        sorted_rates = sorted(rates.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
        
        response = f"📊 **Топ-10 ставок на {ex_id.upper()}:**\n\n"
        for symbol, rate in sorted_rates:
            emoji = "🟢" if rate > 0 else "🔴"
            response += f"{emoji} `{symbol}`: `{rate:.4f}%` \n"
        
        await query.edit_message_text(response, parse_mode="Markdown")

# --- FASTAPI & STARTUP ---

@app.on_event("startup")
async def on_startup():
    global tg_application
    await init_db()
    
    tg_application = Application.builder().token(TOKEN).build()
    tg_application.add_handler(CommandHandler("start", start))
    tg_application.add_handler(CallbackQueryHandler(button_handler))
    
    # Налаштування планувальника (Сканер)
    scheduler = AsyncIOScheduler()
    # Запускаємо scan_market_task кожні 15 хвилин
    scheduler.add_job(scan_market_task, 'interval', minutes=15, args=[tg_application])
    scheduler.start()
    
    await tg_application.initialize()
    if WEBHOOK_URL:
        await tg_application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        logger.info(f"🚀 Webhook set to {WEBHOOK_URL}/webhook")
    await tg_application.start()
    logger.info("✅ Бот та Сканер запущені!")

@app.post("/webhook")
async def webhook_handler(request: Request):
    update = Update.de_json(await request.json(), tg_application.bot)
    await tg_application.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def index():
    return {"status": "FUBot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
