# funding_sources_extra.py
import requests
from datetime import datetime

def safe_time(ms):
    try:
        return datetime.fromtimestamp(int(ms) / 1000)
    except:
        return None


def get_funding_okx():
    url = "https://www.okx.com/api/v5/public/funding-rate-all"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        result = []
        for i in r.json()["data"]:
            if "USDT" not in i["instId"]:
                continue

            result.append({
                "exchange": "OKX",
                "symbol": i["instId"].replace("-SWAP", ""),
                "funding_rate": round(float(i["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(i["nextFundingTime"])
            })
        return result
    except Exception as e:
        print("OKX error:", e)
        return []


def get_funding_kucoin():
    url = "https://api-futures.kucoin.com/api/v1/funding-rate"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        result = []
        for i in r.json()["data"]:
            if not i["symbol"].endswith("USDT"):
                continue

            result.append({
                "exchange": "KuCoin",
                "symbol": i["symbol"],
                "funding_rate": round(float(i["fundingRate"]) * 100, 4),
                "next_funding_time": safe_time(i["time"])
            })
        return result
    except Exception as e:
        print("KuCoin error:", e)
        return []


def get_funding_htx():
    url = "https://api.htx.com/linear-swap-api/v1/swap_funding_rate"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        result = []
        for i in r.json()["data"]:
            result.append({
                "exchange": "HTX",
                "symbol": i["contract_code"],
                "funding_rate": round(float(i["funding_rate"]) * 100, 4),
                "next_funding_time": safe_time(i["funding_time"])
            })
        return result
    except Exception as e:
        print("HTX error:", e)
        return []


def get_funding_gateio():
    url = "https://api.gateio.ws/api/v4/futures/usdt/funding_rate"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        result = []
        for i in r.json():
            result.append({
                "exchange": "Gate.io",
                "symbol": i["contract"],
                "funding_rate": round(float(i["r"]) * 100, 4),
                "next_funding_time": safe_time(i["t"] * 1000)
            })
        return result
    except Exception as e:
        print("Gate.io error:", e)
        return []


def get_funding_bingx():
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        result = []
        for i in r.json()["data"]:
            result.append({
                "exchange": "BingX",
                "symbol": i["symbol"],
                "funding_rate": round(float(i["lastFundingRate"]) * 100, 4),
                "next_funding_time": safe_time(i["nextFundingTime"])
            })
        return result
    except Exception as e:
        print("BingX error:", e)
        return []
