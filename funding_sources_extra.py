# funding_sources_extra.py
import requests
from datetime import datetime
from typing import List, Dict

HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10


def safe_time(ts):
    try:
        if ts is None:
            return datetime.utcnow()
        if ts > 10_000_000_000:
            ts = ts // 1000
        return datetime.fromtimestamp(int(ts))
    except Exception:
        return datetime.utcnow()


# ---------- OKX ----------
def get_funding_okx() -> List[Dict]:
    url = "https://www.okx.com/api/v5/public/funding-rate"
    params = {"instType": "SWAP"}

    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json().get("data", [])

        result = []
        for item in data:
            inst = item.get("instId", "")
            if not inst.endswith("USDT-SWAP"):
                continue

            symbol = inst.replace("-SWAP", "")
            result.append({
                "exchange": "OKX",
                "symbol": symbol,
                "funding_rate": round(float(item["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(item.get("fundingTime"))
            })
        return result

    except Exception as e:
        print("OKX error:", e)
        return []


# ---------- BITGET ----------
def get_funding_bitget() -> List[Dict]:
    url = "https://api.bitget.com/api/v2/mix/market/funding-rate"
    params = {"productType": "USDT-FUTURES"}

    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json().get("data", [])

        result = []
        for item in data:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            result.append({
                "exchange": "Bitget",
                "symbol": symbol,
                "funding_rate": round(float(item["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(item.get("nextFundingTime"))
            })
        return result

    except Exception as e:
        print("Bitget error:", e)
        return []


# ---------- GATE.IO ----------
def get_funding_gateio() -> List[Dict]:
    url = "https://api.gateio.ws/api/v4/futures/usdt/contracts"

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        result = []
        for item in data:
            symbol = item.get("name", "")
            if not symbol.endswith("USDT"):
                continue

            result.append({
                "exchange": "Gate.io",
                "symbol": symbol,
                "funding_rate": round(float(item["funding_rate"]) * 100, 4),
                "next_funding_time": safe_time(item.get("funding_next_apply"))
            })
        return result

    except Exception as e:
        print("Gate.io error:", e)
        return []
