import requests
from datetime import datetime
from proxy import get_proxy_dict

PROXY = get_proxy_dict()

def get_funding_bybit():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data.get("result", {}).get("list", []):
        result.append({
            "symbol": item["symbol"],
            "funding_rate": float(item.get("funding_rate", 0)),
            "next_funding_time": datetime.fromtimestamp(item.get("next_funding_time", 0)),
            "exchange": "Bybit"
        })
    return result

def get_funding_binance():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data:
        result.append({
            "symbol": item["symbol"],
            "funding_rate": float(item.get("lastFundingRate", 0)) * 100,
            "next_funding_time": datetime.fromtimestamp(item.get("nextFundingTime", 0)/1000),
            "exchange": "Binance"
        })
    return result

def get_funding_bitget():
    url = "https://api.bitget.com/api/v2/mix/market/funding-rate?productType=USDT-FUTURES"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data.get("data", []):
        result.append({
            "symbol": item["symbol"],
            "funding_rate": float(item.get("fundingRate", 0)) * 100,
            "next_funding_time": datetime.fromtimestamp(item.get("fundingTime", 0)/1000),
            "exchange": "Bitget"
        })
    return result

def get_funding_mexc():
    url = "https://www.mexc.com/api/v2/market/fundingRate"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data.get("data", []):
        result.append({
            "symbol": item["symbol"],
            "funding_rate": float(item.get("fundingRate", 0)),
            "next_funding_time": datetime.fromtimestamp(item.get("fundingTime", 0)),
            "exchange": "MEXC"
        })
    return result

def get_funding_okx():
    url = "https://www.okx.com/api/v5/public/funding-rate-all"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data.get("data", []):
        result.append({
            "symbol": item["instId"],
            "funding_rate": float(item.get("fundingRate", 0)) * 100,
            "next_funding_time": datetime.fromtimestamp(int(item.get("fundingTime", 0)/1000)),
            "exchange": "OKX"
        })
    return result

def get_funding_kucoin():
    url = "https://api-futures.kucoin.com/api/v1/funding-rate"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data.get("data", []):
        result.append({
            "symbol": item["symbol"],
            "funding_rate": float(item.get("fundingRate", 0)) * 100,
            "next_funding_time": datetime.fromtimestamp(int(item.get("fundingNextTime", 0)/1000)),
            "exchange": "KuCoin"
        })
    return result

def get_funding_htx():
    url = "https://api.htx.com/linear-swap-api/v1/swap_funding_rate"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data.get("data", []):
        result.append({
            "symbol": item["contract_code"],
            "funding_rate": float(item.get("funding_rate", 0)) * 100,
            "next_funding_time": datetime.fromtimestamp(item.get("funding_time", 0)),
            "exchange": "HTX"
        })
    return result

def get_funding_gateio():
    url = "https://api.gateio.ws/api/v4/futures/usdt/funding_rate"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data:
        result.append({
            "symbol": item["contract"],
            "funding_rate": float(item.get("funding_rate", 0)) * 100,
            "next_funding_time": datetime.fromtimestamp(item.get("funding_time", 0)),
            "exchange": "Gate.io"
        })
    return result

def get_funding_bingx():
    url = "https://api.bingx.com/api/v1/funding-rate/all"
    res = requests.get(url, proxies=PROXY, timeout=10)
    data = res.json()
    result = []
    for item in data.get("data", []):
        result.append({
            "symbol": item["symbol"],
            "funding_rate": float(item.get("fundingRate", 0)) * 100,
            "next_funding_time": datetime.fromtimestamp(int(item.get("fundingTime", 0)/1000)),
            "exchange": "BingX"
        })
    return result
