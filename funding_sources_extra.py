# funding_sources_extra.py
import requests
from datetime import datetime

def get_funding_okx():
    url = "https://www.okx.com/api/v5/public/funding-rate"
    params = {"instType": "SWAP"}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()['data']
        result = []
        for item in data:
            symbol = item['instId'].replace('-SWAP', '')
            if symbol.endswith('USDT') or symbol.endswith('USDC'):
                rate = float(item['fundingRate']) * 100
                next_time = datetime.fromtimestamp(int(item['fundingTime']) // 1000)
                result.append({
                    "exchange": "OKX",
                    "symbol": symbol,
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("OKX error:", e)
        return []

def get_funding_kucoin():
    url = "https://api-futures.kucoin.com/api/v1/funding-rate/all"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()['data']
        result = []
        for item in data:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                rate = float(item['fundingRate']) * 100
                next_time = datetime.fromtimestamp(item['time'] // 1000)
                result.append({
                    "exchange": "KuCoin",
                    "symbol": symbol,
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("KuCoin error:", e)
        return []

def get_funding_htx():
    url = "https://api.htx.com/linear-swap-api/v1/swap_batch_funding_rate"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()['data']
        result = []
        for item in data:
            symbol = item['contract_code']
            if symbol.endswith('-USDT'):
                rate = float(item['funding_rate']) * 100
                next_time = datetime.fromtimestamp(int(item['next_funding_time']) // 1000)
                result.append({
                    "exchange": "HTX",
                    "symbol": symbol,
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("HTX error:", e)
        return []

def get_funding_gateio():
    url = "https://api.gateio.ws/api/v4/futures/usdt/funding_rate"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        result = []
        for item in data:
            symbol = item['contract']
            if symbol.endswith('_USDT'):
                rate = float(item['r']) * 100
                next_time = datetime.fromtimestamp(item['t'])
                result.append({
                    "exchange": "Gate.io",
                    "symbol": symbol,
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("Gate.io error:", e)
        return []

def get_funding_bingx():
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()['data']
        result = []
        for item in data:
            symbol = item['symbol']
            if symbol.endswith('-USDT'):
                rate = float(item['lastFundingRate']) * 100
                next_time = datetime.fromtimestamp(int(item['nextFundingTime']) // 1000)
                result.append({
                    "exchange": "BingX",
                    "symbol": symbol,
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("BingX error:", e)
        return []