# funding_sources.py
import requests
from datetime import datetime

TIMEOUT = 10


def _safe_json(response):
    try:
        return response.json()
    except Exception:
        return None


# =========================
# BYBIT
# =========================
def get_funding_bybit():
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "linear"}

    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = _safe_json(r)

        items = data.get("result", {}).get("list", []) if isinstance(data, dict) else []
        result = []

        for item in items:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            rate = float(item.get("fundingRate", 0)) * 100
            ts = int(item.get("nextFundingTime", 0))
            next_time = datetime.fromtimestamp(ts / 1000) if ts else None

            result.append({
                "exchange": "Bybit",
                "symbol": symbol,
                "funding_rate": round(rate, 4),
                "next_funding_time": next_time
            })

        return result

    except Exception as e:
        print("Bybit error:", e)
        return []


# =========================
# BINANCE
# =========================
def get_funding_binance():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"

    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = _safe_json(r)

        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            rate = float(item.get("lastFundingRate", 0)) * 100
            ts = int(item.get("nextFundingTime", 0))
            next_time = datetime.fromtimestamp(ts / 1000) if ts else None

            result.append({
                "exchange": "Binance",
                "symbol": symbol,
                "funding_rate": round(rate, 4),
                "next_funding_time": next_time
            })

        return result

    except Exception as e:
        print("Binance error:", e)
        return []


# =========================
# BITGET
# =========================
def get_funding_bitget():
    url = "https://api.bitget.com/api/v2/mix/market/current-fund-rate"
    params = {"productType": "umcbl"}

    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = _safe_json(r)

        items = data.get("data", []) if isinstance(data, dict) else []
        result = []

        for item in items:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            rate = float(item.get("fundingRate", 0)) * 100
            ts = int(item.get("fundingTime", 0))
            next_time = datetime.fromtimestamp(ts / 1000) if ts else None

            result.append({
                "exchange": "Bitget",
                "symbol": symbol,
                "funding_rate": round(rate, 4),
                "next_funding_time": next_time
            })

        return result

    except Exception as e:
        print("Bitget error:", e)
        return []


# =========================
# MEXC (ВАЖЛИВО: тут LIST)
# =========================
def get_funding_mexc():
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"

    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = _safe_json(r)

        items = data.get("data", []) if isinstance(data, dict) else []
        result = []

        for item in items:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            rate = float(item.get("fundingRate", 0)) * 100
            ts = int(item.get("fundingTime", 0))
            next_time = datetime.fromtimestamp(ts / 1000) if ts else None

            result.append({
                "exchange": "MEXC",
                "symbol": symbol,
                "funding_rate": round(rate, 4),
                "next_funding_time": next_time
            })

        return result

    except Exception as e:
        print("MEXC error:", e)
        return []
