# funding_sources_all.py
import requests
from datetime import datetime
import pytz

# =========================
# ПРОКСІ
# =========================
# Замінити на свій робочий британський проксі
PROXY_URL = "http://user:pass@proxy:port"
PROXIES = {
    "http": PROXY_URL,
    "https": PROXY_URL
}

# =========================
# HELPER ФУНКЦІЯ
# =========================
def fetch_json(url):
    try:
        response = requests.get(url, proxies=PROXIES, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"{url} error:", e)
        return None

# =========================
# ФУНКЦІЇ ДЛЯ КОЖНОЇ БІРЖІ
# =========================
def get_funding_bybit():
    url = "https://api.bybit.com/v2/public/funding/prev-funding-rate?symbol=BTCUSDT"
    data = fetch_json(url)
    if not data or 'result' not in data:
        return []
    rate = float(data['result']['funding_rate']) * 100
    time_str = datetime.fromtimestamp(data['result']['funding_time'], pytz.UTC)
    return [{"exchange": "Bybit", "symbol": "BTCUSDT", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_binance():
    url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"
    data = fetch_json(url)
    if not data:
        return []
    last = data[-1]
    rate = float(last['fundingRate']) * 100
    time_str = datetime.fromtimestamp(last['fundingTime']/1000, pytz.UTC)
    return [{"exchange": "Binance", "symbol": "BTCUSDT", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_bitget():
    url = "https://api.bitget.com/api/mix/v1/market/funding_rate?symbol=BTCUSDT_UMCBL"
    data = fetch_json(url)
    if not data or 'data' not in data:
        return []
    last = data['data']
    rate = float(last['fundingRate']) * 100
    time_str = datetime.fromtimestamp(int(last['fundingTime'])/1000, pytz.UTC)
    return [{"exchange": "Bitget", "symbol": "BTCUSDT", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_mexc():
    url = "https://contract.mexc.com/api/v1/private/funding-rate?symbol=BTC_USDT"
    data = fetch_json(url)
    if not data or 'data' not in data:
        return []
    last = data['data'][0]
    rate = float(last['fundingRate']) * 100
    time_str = datetime.fromtimestamp(last['fundingTime']/1000, pytz.UTC)
    return [{"exchange": "MEXC", "symbol": "BTC_USDT", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_okx():
    url = "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"
    data = fetch_json(url)
    if not data or 'data' not in data:
        return []
    last = data['data'][0]
    rate = float(last['fundingRate']) * 100
    time_str = datetime.strptime(last['fundingTime'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC)
    return [{"exchange": "OKX", "symbol": "BTC-USDT-SWAP", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_kucoin():
    url = "https://api-futures.kucoin.com/api/v1/funding-rate-history?symbol=XBTUSDTM&limit=1"
    data = fetch_json(url)
    if not data or 'data' not in data:
        return []
    last = data['data'][0]
    rate = float(last['fundingRate']) * 100
    time_str = datetime.fromtimestamp(last['fundingTime']/1000, pytz.UTC)
    return [{"exchange": "KuCoin", "symbol": "XBTUSDTM", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_htx():
    url = "https://api.hadax.com/v1/futures/funding_rate/BTCUSDT"
    data = fetch_json(url)
    if not data or 'fundingRate' not in data:
        return []
    rate = float(data['fundingRate']) * 100
    time_str = datetime.utcnow().replace(tzinfo=pytz.UTC)
    return [{"exchange": "HTX", "symbol": "BTCUSDT", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_gateio():
    url = "https://api.gateio.ws/api/v4/futures/usdt/funding_rate?contract=BTC_USDT"
    data = fetch_json(url)
    if not data or len(data) == 0:
        return []
    last = data[-1]
    rate = float(last['rate']) * 100
    time_str = datetime.fromtimestamp(last['time'], pytz.UTC)
    return [{"exchange": "Gate.io", "symbol": "BTC_USDT", "funding_rate": rate, "next_funding_time": time_str}]

def get_funding_bingx():
    url = "https://api.bingx.com/api/v1/funding_rate?symbol=BTCUSDT"
    data = fetch_json(url)
    if not data or 'data' not in data:
        return []
    last = data['data'][-1]
    rate = float(last['fundingRate']) * 100
    time_str = datetime.fromtimestamp(last['fundingTime']/1000, pytz.UTC)
    return [{"exchange": "BingX", "symbol": "BTCUSDT", "funding_rate": rate, "next_funding_time": time_str}]

# =========================
# ФУНКЦІЯ ОБ'ЄДНАННЯ ВСІХ БІРЖ
# =========================
def get_all_funding():
    functions = [
        get_funding_bybit, get_funding_binance, get_funding_bitget, get_funding_mexc,
        get_funding_okx, get_funding_kucoin, get_funding_htx, get_funding_gateio, get_funding_bingx
    ]
    result = []
    for func in functions:
        try:
            result.extend(func())
        except Exception as e:
            print(f"{func.__name__} error:", e)
    return result

# =========================
# ФОРМАТУВАННЯ ПОВІДОМЛЕННЯ ДЛЯ БОТА
# =========================
FREE_THRESHOLD = 1.5  # поріг для FREE плану

def format_funding_message(funding_list, plan, lang=None):
    funding_list.sort(key=lambda x: x.get("funding_rate", 0), reverse=True)
    lines = []
    for f in funding_list[:10]:
        rate = f.get("funding_rate", 0)
        time_str = f.get("next_funding_time", datetime.now()).strftime("%H:%M")
        symbol = f.get("symbol", "")
        exchange = f.get("exchange", "")
        if plan == "FREE" and rate > FREE_THRESHOLD:
            line = f"{rate:.2f}% о {time_str} на {exchange}"
        else:
            line = f"{rate:.2f}% о {time_str} → {symbol} ({exchange})"
        lines.append(line)
    return "\n".join(lines) if lines else "Немає даних по funding rate"
