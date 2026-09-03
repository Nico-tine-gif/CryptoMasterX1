import requests
import json

def get_crypto_price(symbol):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    try:
        response = requests.get(url)
        data = response.json()
        return data[symbol]['usd']
    except:
        return None

symbols = ['bitcoin', 'ethereum', 'cardano']
for coin in symbols:
    price = get_crypto_price(coin)
    if price:
        print(f"{coin.capitalize()}: ${price:,.2f}")

