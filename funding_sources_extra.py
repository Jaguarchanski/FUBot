# funding_sources_extra.py
import requests
from datetime import datetime


def safe_ts(ts):
    """Конвертація timestamp (ms або s) → datetime або None"""
    if not ts:
        return None
    ts = int(ts)
    if ts > 10_000_000_000:
        ts //= 1000
    return datetime.fromtimestamp(ts)


# ---------- OKX ----------
def get_funding_okx():
    url = "https://www.okx.com/api/v5/public/funding-rate"
    params = {"instType": "SWAP"}
    result = []

    try:
        r = requests.get(url, params=params, timeout=10)
        for item in r.json().get("data", []):
            inst = item.get("instId", "")
            if not inst.endswith("-SWAP"):
                continue

            base = inst.replace("-SWAP", "")
            if not (base.endswith("USDT") or base.endswith("USDC")):
                continue

            rate = float(item.get("fundingRate", 0)) * 100

            result.append({
                "exchange": "OKX",
                "symbol": base,
                "funding_rate": round(rate, 4),
                "next_funding_time": safe_ts(item.get("fundingTime"))
            })
    except Exception as e:
        print("OKX error:", e)

    return result


# ---------- KuCoin ----------
def get_funding_kucoin():
    url = "https://api-futures.kucoin.com/api/v1/contracts/active"
    result = []

    try:
        r = requests.get(url, timeout=10)
        for item in r.json().get("data", []):
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDT"):
                continue

            rate = float(item.get("fundingFeeRate", 0)) * 100

            result.append({
                "exchange": "KuCoin",
                "symbol": symbol,
                "funding_rate": round(rate, 4),
                "next_funding_time": None
            })
    except Exception as e:
        print("KuCoin error:", e)

    return result


# ---------- HTX (Huobi) ----------
def get_funding_htx():
    url = "https://api.htx.com/linear-swap-api/v1/swap_batch_funding_rate"
    result = []

    try:
        r = requests.get(url, timeout=10)
        for item in r.json().get("data", []):
            symbol = item.get("contract_code", "")
            if not symbol.endswith("-USDT"):
                continue

            rate = float(item.get("funding_rate", 0)) * 100

            result.append({
                "exchange": "HTX",
                "symbol": symbol.replace("-", ""),
                "funding_rate": round(rate, 4),
                "next_funding_time": safe_ts(item.get("next_funding_time"))
            })
    except Exception as e:
        print("HTX error:", e)

    return result


# ---------- Gate.io ----------
def get_funding_gateio():
    url = "https://api.gateio.ws/api/v4/futures/usdt/funding_rate"
    result = []

    try:
        r = requests.get(url, timeout=10)
        for item in r.json():
            symbol = item.get("contract", "")
            if not symbol.endswith("_USDT"):
                continue

            rate = float(item.get("r", 0)) * 100

            result.append({
                "exchange": "Gate.io",
                "symbol": symbol.replace("_", ""),
                "funding_rate": round(rate, 4),
                "next_funding_time": safe_ts(item.get("t"))
            })
    except Exception as e:
        print("Gate.io error:", e)

    return result


# ---------- BingX ----------
def get_funding_bingx():
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex"
    result = []

    try:
        r = requests.get(url, timeout=10)
        for item in r.json().get("data", []):
            symbol = item.get("symbol", "")
            if not symbol.endswith("-USDT"):
                continue

            if item.get("lastFundingRate") is None:
                continue

            rate = float(item["lastFundingRate"]) * 100

            result.append({
                "exchange": "BingX",
                "symbol": symbol.replace("-", ""),
                "funding_rate": round(rate, 4),
                "next_funding_time": safe_ts(item.get("nextFundingTime"))
            })
    except Exception as e:
        print("BingX error:", e)

    return result
