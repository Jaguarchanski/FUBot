# funding_sources.py
import requests
from datetime import datetime
from typing import List, Dict

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def safe_time(ms):
    try:
        return datetime.fromtimestamp(int(ms) / 1000)
    except:
        return None


def get_funding_binance() -> List[Dict]:
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        result = []

        for i in r.json():
            if not i["symbol"].endswith("USDT"):
                continue

            result.append({
                "exchange": "Binance",
                "symbol": i["symbol"],
                "funding_rate": round(float(i["lastFundingRate"]) * 100, 4),
                "next_funding_time": safe_time(i["nextFundingTime"])
            })
        return result
    except Exception as e:
        print("Binance error:", e)
        return []


def get_funding_bybit():
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "linear"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()

        data = r.json()["result"]["list"]
        result = []

        for i in data:
            if not i["symbol"].endswith("USDT"):
                continue

            result.append({
                "exchange": "Bybit",
                "symbol": i["symbol"],
                "funding_rate": round(float(i.get("fundingRate", 0)) * 100, 4),
                "next_funding_time": safe_time(i.get("nextFundingTime"))
            })
        return result
    except Exception as e:
        print("Bybit error:", e)
        return []


def get_funding_bitget():
    url = "https://api.bitget.com/api/v2/mix/market/funding-rate"
    params = {"productType": "USDT-FUTURES"}

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        result = []
        for i in r.json()["data"]:
            if not i["symbol"].endswith("USDT"):
                continue

            result.append({
                "exchange": "Bitget",
                "symbol": i["symbol"],
                "funding_rate": round(float(i["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(i["nextFundingTime"])
            })
        return result
    except Exception as e:
        print("Bitget error:", e)
        return []


def get_funding_mexc():
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        result = []
        for i in r.json()["data"]:
            if not i["symbol"].endswith("USDT"):
                continue

            result.append({
                "exchange": "MEXC",
                "symbol": i["symbol"],
                "funding_rate": round(float(i["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(i["fundingTime"])
            })
        return result
    except Exception as e:
        print("MEXC error:", e)
        return []
