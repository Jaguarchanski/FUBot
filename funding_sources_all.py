import requests
import asyncio

# Проксі (можна з proxy.py імпортувати)
PROXIES = {
    'http': 'http://user:pass@proxy_ip:proxy_port',
    'https': 'http://user:pass@proxy_ip:proxy_port'
}

# Приклад бірж
EXCHANGES = ['binance', 'bybit', 'okx']

async def fetch_binance():
    url = "https://fapi.binance.com/fapi/v1/fundingRate?limit=5"
    try:
        r = requests.get(url, proxies=PROXIES, timeout=5)
        data = r.json()
        return [{'exchange': 'Binance', 'symbol': x['symbol'], 'fundingRate': x['fundingRate']} for x in data]
    except Exception as e:
        return [{'exchange': 'Binance', 'error': str(e)}]

async def fetch_bybit():
    url = "https://api.bybit.com/v2/public/funding/prev-funding-rate?limit=5"
    try:
        r = requests.get(url, proxies=PROXIES, timeout=5)
        data = r.json().get('result', [])
        return [{'exchange': 'Bybit', 'symbol': x['symbol'], 'fundingRate': x['fundingRate']} for x in data]
    except Exception as e:
        return [{'exchange': 'Bybit', 'error': str(e)}]

async def fetch_okx():
    url = "https://www.okx.com/api/v5/public/funding-rate?instType=FUTURES"
    try:
        r = requests.get(url, proxies=PROXIES, timeout=5)
        data = r.json().get('data', [])
        return [{'exchange': 'OKX', 'symbol': x['instId'], 'fundingRate': x['fundingRate']} for x in data]
    except Exception as e:
        return [{'exchange': 'OKX', 'error': str(e)}]

async def get_all_funding():
    results = await asyncio.gather(fetch_binance(), fetch_bybit(), fetch_okx())
    # Об’єднуємо всі результати
    funding_list = [item for sublist in results for item in sublist]
    return funding_list

def format_funding_message(funding_list, plan=None, lang='en'):
    # Просте форматування
    messages = []
    for f in funding_list:
        if 'error' in f:
            messages.append(f"{f['exchange']}: Error: {f['error']}")
        else:
            messages.append(f"{f['exchange']} | {f['symbol']} | {f['fundingRate']}")
    return "\n".join(messages)
