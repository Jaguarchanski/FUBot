# funding_sources.py
import requests
from datetime import datetime

def get_funding_bybit():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()['result']['list']
        result = []
        for item in data:
            if item['symbol'].endswith('USDT'):
                rate = float(item.get('fundingRate', 0)) * 100
                next_time = datetime.fromtimestamp(int(item.get('nextFundingTime', 0)) // 1000)
                result.append({
                    "exchange": "Bybit",
                    "symbol": item['symbol'],
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("Bybit error:", e)
        return []

def get_funding_binance():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        result = []
        for item in data:
            if item['symbol'].endswith('USDT'):
                rate = float(item['lastFundingRate']) * 100
                next_time = datetime.fromtimestamp(int(item['nextFundingTime']) // 1000)
                result.append({
                    "exchange": "Binance",
                    "symbol": item['symbol'],
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("Binance error:", e)
        return []

def get_funding_bitget():
    url = "https://api.bitget.com/api/v2/mix/market/current-fund-rate"
    params = {"productType": "umcbl"}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()['data']
        result = []
        for item in data:
            if item['symbol'].endswith('USDT'):
                rate = float(item['fundingRate']) * 100
                next_time = datetime.fromtimestamp(int(item['fundingTime']) // 1000)
                result.append({
                    "exchange": "Bitget",
                    "symbol": item['symbol'],
                    "funding_rate": round(rate, 4),
                    "next_funding_time": next_time
                })
        return result
    except Exception as e:
        print("Bitget error:", e)
        return []

def get_funding_mexc():
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()['data']
        result = []
        for symbol, item in data.items():
            if symbol.endswith('USDT'):
                rate = float(item['fundingRate']) * 100
                next_time = datetime.fromtimestamp(item['fundingTime'] // 1000)
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