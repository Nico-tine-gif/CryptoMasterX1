import requests

def get_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    try:
        return requests.get(url).json()[coin]['usd']
    except:
        return None

# Your portfolio: [coin, amount_held]
portfolio = [
    ['bitcoin', 0.5],
    ['ethereum', 5.0],
    ['cardano', 1000],
    ['solana', 20]
]

total_value = 0
print("💼 Portfolio Value")
print("-" * 40)
for coin, amount in portfolio:
    price = get_price(coin)
    if price:
        value = price * amount
        total_value += value
        print(f"{coin.capitalize():12} ${price:>8,.2f} x {amount:>8} = ${value:>12,.2f}")

print("-" * 40)
print(f"{'TOTAL':12} {'':>8} {'':>8} = ${total_value:>12,.2f}")
