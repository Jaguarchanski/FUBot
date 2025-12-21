import requests
from proxy import get_proxy

PROXY = get_proxy()
TIMEOUT = 15

def fetch(url):
    try:
        r = requests.get(url, proxies=PROXY, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ===== BINANCE =====
def binance():
    data = fetch("https://fapi.binance.com/fapi/v1/premiumIndex")
    if isinstance(data, list):
        return [
            {
                "exchange": "Binance",
                "symbol": i["symbol"],
                "funding": float(i["lastFundingRate"])
            }
            for i in data
        ]
    return []

# ===== BYBIT =====
def bybit():
    data = fetch("https://api.bybit.com/v5/market/tickers?category=linear")
    result = []
    if "result" in data:
        for i in data["result"]["list"]:
            if i.get("fundingRate"):
                result.append({
                    "exchange": "Bybit",
                    "symbol": i["symbol"],
                    "funding": float(i["fundingRate"])
                })
    return result

# ===== OKX =====
def okx():
    data = fetch("https://www.okx.com/api/v5/public/funding-rate")
    result = []
    if "data" in data:
        for i in data["data"]:
            result.append({
                "exchange": "OKX",
                "symbol": i["instId"],
                "funding": float(i["fundingRate"])
            })
    return result

# ===== GATE =====
def gate():
    data = fetch("https://api.gateio.ws/api/v4/futures/usdt/contracts")
    result = []
    if isinstance(data, list):
        for i in data:
            if i.get("funding_rate"):
                result.append({
                    "exchange": "Gate",
                    "symbol": i["name"],
                    "funding": float(i["funding_rate"])
                })
    return result

# ===== MEXC =====
def mexc():
    data = fetch("https://contract.mexc.com/api/v1/contract/funding_rate")
    result = []
    if "data" in data:
        for i in data["data"]:
            result.append({
                "exchange": "MEXC",
                "symbol": i["symbol"],
                "funding": float(i["fundingRate"])
            })
    return result

# ===== ALL =====
def get_all_funding():
    exchanges = [
        binance,
        bybit,
        okx,
        gate,
        mexc
    ]

    all_data = []
    for ex in exchanges:
        try:
            res = ex()
            all_data.extend(res)
            print(f"[OK] {ex.__name__}: {len(res)}")
        except Exception as e:
            print(f"[FAIL] {ex.__name__}: {e}")

    return all_data
