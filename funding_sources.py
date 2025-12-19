# funding_sources.py
import requests
from datetime import datetime
from typing import List, Dict

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def _safe_time(ts):
    try:
        if not ts:
            return None
        return datetime.fromtimestamp(int(ts) / 1000)
    except Exception:
        return None


# ---------------- BYBIT ----------------
def get_funding_bybit() -> List[Dict]:
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "linear"}

    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("result", {}).get("list", [])
    except Exception as e:
        print("Bybit error:", e)
        return []

    result = []
    for i in data:
        if not i.get("symbol", "").endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "Bybit",
                "symbol": i["symbol"],
                "funding_rate": round(float(i.get("fundingRate", 0)) * 100, 4),
                "next_funding_time": _safe_time(i.get("nextFundingTime"))
            })
        except Exception:
            continue

    return result


# ---------------- BINANCE (без проксі) ----------------
def get_funding_binance() -> List[Dict]:
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []  # ❗ не валимо бот
        data = r.json()
    except Exception as e:
        print("Binance error:", e)
        return []

    result = []
    for i in data:
        if not i.get("symbol", "").endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "Binance",
                "symbol": i["symbol"],
                "funding_rate": round(float(i["lastFundingRate"]) * 100, 4),
                "next_funding_time": _safe_time(i.get("nextFundingTime"))
            })
        except Exception:
            continue

    return result


# ---------------- BITGET (ВИПРАВЛЕНО) ----------------
def get_funding_bitget() -> List[Dict]:
    url = "https://api.bitget.com/api/v2/mix/market/funding-rate"
    params = {"productType": "USDT-FUTURES"}

    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        print("Bitget error:", e)
        return []

    result = []
    for i in data:
        symbol = i.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "Bitget",
                "symbol": symbol,
                "funding_rate": round(float(i.get("fundingRate", 0)) * 100, 4),
                "next_funding_time": _safe_time(i.get("nextFundingTime"))
            })
        except Exception:
            continue

    return result


# ---------------- MEXC ----------------
def get_funding_mexc() -> List[Dict]:
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", {})
    except Exception as e:
        print("MEXC error:", e)
        return []

    result = []
    for symbol, i in data.items():
        if not symbol.endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "MEXC",
                "symbol": symbol,
                "funding_rate": round(float(i.get("fundingRate", 0)) * 100, 4),
                "next_funding_time": _safe_time(i.get("fundingTime"))
            })
        except Exception:
            continue

    return result
