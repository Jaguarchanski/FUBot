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
        'pro_success': "Дякую за оплату!\nВи PRO до {date} ✅",
        'settings_saved': "Налаштування збережено!",
        'auto_message': "Авто-сповіщення:",
        'no_funding': "Немає актуальних funding вище порогу",
        'back_button': "Назад ←",
        'choose_exchange': "Оберіть біржу:",
        'choose_threshold': "Мінімальний поріг funding (%):",
        'choose_interval': "Інтервал сповіщень:",
        'choose_timezone': "Часовий пояс:",
        'filter_menu': "Налаштування фільтру:",
        'set_timezone': "⏰ Встановити часовий пояс",
        'select_exchanges': "🏦 Вибрати біржі",
        'set_threshold': "🔢 Встановити поріг",
        'main_menu': "Головне меню",
        'choose_exchanges': "Оберіть біржі, які вас цікавлять:",
        'set_threshold_text': "Встановіть мінімальний поріг funding:",
        'choose_timezone': "Оберіть ваш часовий пояс:"
    },
    'en': {
        'welcome': "Hello! Choose language:",
        'start_message': "Funding rates from 9 exchanges + alerts\nCustomize below ↓",
        'filter_button': "Filter ⚙️",
        'top_funding_button': "Top Funding 🔥",
        'account_button': "Account 👤",
        'get_pro_button': "Get PRO — 50 USDT/month",
        'early_bird': "Congrats! You are #{num} of 500 early-birds!\nFree PRO for 30 days 🎉",
        'pro_success': "Payment successful!\nYou are PRO until {date} ✅",
        'settings_saved': "Settings saved!",
        'auto_message': "Auto-alert:",
        'no_funding': "No funding rates above threshold",
        'back_button': "Back ←",
        'choose_exchange': "Choose exchange:",
        'choose_threshold': "Minimum funding threshold (%):",
        'choose_interval': "Notification interval:",
        'choose_timezone': "Timezone:",
        'filter_menu': "Filter settings:",
        'set_timezone': "⏰ Set Timezone",
        'select_exchanges': "🏦 Select Exchanges",
        'set_threshold': "🔢 Set Threshold",
        'main_menu': "Main Menu",
        'choose_exchanges': "Select exchanges you are interested in:",
        'set_threshold_text': "Set minimum funding threshold:",
        'choose_timezone': "Select your timezone:"
    }
}

def get_text(lang, key, **kwargs):
    text = TEXTS.get(lang, TEXTS['uk']).get(key, key)
    return text.format(**kwargs) if kwargs else text
