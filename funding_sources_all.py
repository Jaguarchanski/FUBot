from datetime import datetime
from proxy import session  # використання проксі для запитів

# ---- Приклад імпортів бірж ----
import requests

def get_funding_bybit():
    try:
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        res = session.get(url, timeout=5).json()
        result = []
        for d in res.get("result", []):
            result.append({
                "symbol": d.get("symbol"),
                "funding_rate": float(d.get("funding_rate", 0)) * 100,
                "next_funding_time": datetime.fromtimestamp(d.get("next_funding_time", 0)/1000),
                "exchange": "Bybit"
            })
        return result
    except Exception as e:
        print("Bybit error:", e)
        return []

# --- Інші біржі: Binance, Bitget, MEXC, OKX, KuCoin, HTX, Gate.io, BingX ---
# Ті ж самі функції робимо через session.get() і парсимо JSON
def get_funding_binance():
    try:
        url = "https://fapi.binance.com/fapi/v1/premiumIndex"
        res = session.get(url, timeout=5).json()
        result = []
        for d in res:
            result.append({
                "symbol": d.get("symbol"),
                "funding_rate": float(d.get("lastFundingRate", 0)) * 100,
                "next_funding_time": datetime.fromtimestamp(d.get("nextFundingTime", 0)/1000),
                "exchange": "Binance"
            })
        return result
    except Exception as e:
        print("Binance error:", e)
        return []

# --- Теж саме для всіх інших бірж ---
def get_funding_bitget(): return []
def get_funding_mexc(): return []
def get_funding_okx(): return []
def get_funding_kucoin(): return []
def get_funding_htx(): return []
def get_funding_gateio(): return []
def get_funding_bingx(): return []

# ---- Об'єднана функція ----
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
