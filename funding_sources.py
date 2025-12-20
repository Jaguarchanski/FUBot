# funding_sources.py
import requests
from datetime import datetime
from typing import List, Dict

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TIMEOUT = 10


def safe_time(ts) -> datetime:
    try:
        if ts is None:
            return datetime.utcnow()
        if ts > 10_000_000_000:  # ms
            ts = ts // 1000
        return datetime.fromtimestamp(int(ts))
    except Exception:
        return datetime.utcnow()


# ---------- BINANCE (працює без проксі) ----------
def get_funding_binance() -> List[Dict]:
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {"limit": 1000}

    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        result = []
        for item in data:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            result.append({
                "exchange": "Binance",
                "symbol": symbol,
                "funding_rate": round(float(item["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(item.get("fundingTime"))
            })
        return result

    except Exception as e:
        print("Binance error:", e)
        return []


# ---------- BYBIT (часто блокує, але пробуємо) ----------
def get_funding_bybit() -> List[Dict]:
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "linear"}

    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json().get("result", {}).get("list", [])

        result = []
        for item in data:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            result.append({
                "exchange": "Bybit",
                "symbol": symbol,
                "funding_rate": round(float(item.get("fundingRate", 0)) * 100, 4),
                "next_funding_time": safe_time(item.get("nextFundingTime"))
            })
        return result

    except Exception as e:
        print("Bybit error:", e)
        return []


# ---------- MEXC (ВАЖЛИВО: data = list) ----------
def get_funding_mexc() -> List[Dict]:
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json().get("data", [])

        result = []
        for item in data:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            result.append({
                "exchange": "MEXC",
                "symbol": symbol,
                "funding_rate": round(float(item["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(item.get("fundingTime"))
            })
        return result

    except Exception as e:
        print("MEXC error:", e)
        return []
