# funding_sources_extra.py
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


# ---------------- OKX ----------------
def get_funding_okx() -> List[Dict]:
    url = "https://www.okx.com/api/v5/public/funding-rate"
    params = {"instType": "SWAP"}

    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        print("OKX error:", e)
        return []

    result = []
    for i in data:
        inst = i.get("instId", "")
        if not inst.endswith("USDT-SWAP"):
            continue

        try:
            result.append({
                "exchange": "OKX",
                "symbol": inst.replace("-SWAP", ""),
                "funding_rate": round(float(i.get("fundingRate", 0)) * 100, 4),
                "next_funding_time": _safe_time(i.get("fundingTime"))
            })
        except Exception:
            continue

    return result


# ---------------- KUCOIN ----------------
def get_funding_kucoin() -> List[Dict]:
    url = "https://api-futures.kucoin.com/api/v1/contracts/active"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        print("KuCoin error:", e)
        return []

    result = []
    for i in data:
        symbol = i.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "KuCoin",
                "symbol": symbol,
                "funding_rate": round(float(i.get("fundingFeeRate", 0)) * 100, 4),
                "next_funding_time": None
            })
        except Exception:
            continue

    return result


# ---------------- HTX (Huobi) ----------------
def get_funding_htx() -> List[Dict]:
    url = "https://api.htx.com/linear-swap-api/v1/swap_batch_funding_rate"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        print("HTX error:", e)
        return []

    result = []
    for i in data:
        symbol = i.get("contract_code", "")
        if not symbol.endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "HTX",
                "symbol": symbol,
                "funding_rate": round(float(i.get("funding_rate", 0)) * 100, 4),
                "next_funding_time": _safe_time(i.get("next_funding_time"))
            })
        except Exception:
            continue

    return result


# ---------------- GATE.IO (FIX) ----------------
def get_funding_gateio() -> List[Dict]:
    url = "https://api.gateio.ws/api/v4/futures/usdt/contracts"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print("Gate.io error:", e)
        return []

    result = []
    for i in data:
        symbol = i.get("name", "")
        if not symbol.endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "Gate.io",
                "symbol": symbol,
                "funding_rate": round(float(i.get("funding_rate", 0)) * 100, 4),
                "next_funding_time": None
            })
        except Exception:
            continue

    return result


# ---------------- BINGX ----------------
def get_funding_bingx() -> List[Dict]:
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        print("BingX error:", e)
        return []

    result = []
    for i in data:
        symbol = i.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue

        try:
            result.append({
                "exchange": "BingX",
                "symbol": symbol,
                "funding_rate": round(float(i.get("lastFundingRate", 0)) * 100, 4),
                "next_funding_time": _safe_time(i.get("nextFundingTime"))
            })
        except Exception:
            continue

    return result
