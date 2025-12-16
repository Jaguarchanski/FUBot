# i18n.py
TEXTS = {
    'uk': {
        'welcome': "Вітаю! Оберіть мову:",
        'start_message': "Фандинг з 9 бірж + сповіщення\nНалаштуйте під себе ↓",
        'filter_button': "Фільтр ⚙️",
        'top_funding_button': "Топ фандинг 🔥",
        'account_button': "Акаунт 👤",
        'get_pro_button': "Отримати PRO — 50 USDT/міс",
        'early_bird': "Вітаю! Ви №{num} з 500 early-bird!\nБезкоштовно PRO на 30 днів 🎉",
        'early_bird_end': "500 безкоштовних PRO закінчилися!\nТепер 50 USDT/міс",
        'pro_success': "Дякую за оплату!\nВи PRO до {date} ✅",
        'settings_saved': "Налаштування збережено!",
        'auto_message': "Авто-сповіщення:",
        'no_funding': "Немає актуальних funding вище порогу"
    },
    'en': {
        'welcome': "Hello! Choose language:",
        'start_message': "Funding rates from 9 exchanges + alerts\nCustomize below ↓",
        'filter_button': "Filter ⚙️",
        'top_funding_button': "Top Funding 🔥",
        'account_button': "Account 👤",
        'get_pro_button': "Get PRO — 50 USDT/month",
        'early_bird': "Congrats! You are #{num} of 500 early-birds!\nFree PRO for 30 days 🎉",
        'early_bird_end': "500 free PRO spots are over!\nNow 50 USDT/month",
        'pro_success': "Payment successful!\nYou are PRO until {date} ✅",
        'settings_saved': "Settings saved!",
        'auto_message': "Auto-alert:",
        'no_funding': "No funding rates above threshold"
    }
}

def get_text(lang, key, **kwargs):
    text = TEXTS.get(lang, TEXTS['uk']).get(key, key)
    return text.format(**kwargs) if kwargs else text