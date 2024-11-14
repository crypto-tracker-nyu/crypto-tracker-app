"""Main application"""
# TODO: split up?

from flask import Flask, request, jsonify
import time
from flask_cors import CORS
import requests
import os
import datetime

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

@app.route("/time")
def getTime():
    return {"time": time.time()}

COIN_GECKO_KEY = os.environ["COIN_GECKO_KEY"]
NEWS_KEY = os.environ["NEWS_KEY"]

# React -> Flask
# TODO: how to get parameters and search options from react into flask?
# current strategy, query backend routes using ? params

# TODO: for all requests.text returns, maybe edit to whatever kind of output we want on the page
# decide at next meeting?

@app.route("/")
def hello():

    response = requests.get(f"https://api.coingecko.com/api/v3/ping",
                            params={"x_cg_demo_api_key":COIN_GECKO_KEY},
                            headers={"accept": "application/json"})

    return response.text

@app.route("/top100")
def top10():
    # How to use right now: localhost:5001/top10
    response = requests.get(f"https://api.coingecko.com/api/v3/coins/markets",
                            params={
                                "vs_currency":"usd",
                                "order": "market_cap_desc",
                                "per_page": 10,
                                "page": 1,
                                "x_cg_demo_api_key":COIN_GECKO_KEY
                            },
                            headers={"accept": "application/json"})
    top10 = []
    for item in response.json():
        top10.append({
            "id": item.get("id"),
            "rank": item.get("market_cap_rank"),
            "coin": {
                "name": item.get("name"),
                "image": item.get("image"),
                "symbol": item.get("symbol"),
            },
            "current_price": item.get("current_price"),
            "market_cap": item.get("market_cap"),
            "price_change_percentage_24h": item.get("price_change_percentage_24h"),
        })
    return top10

@app.route("/list")
def list():
    """Get a list of supported coins on CoinGecko with coins id, name and symbol"""
    # How to use right now: localhost:5001/list
    response = requests.get(f"https://api.coingecko.com/api/v3/coins/list",
                            headers={"accept": "application/json"})
    coin_list = [coin for coin in response.json()]
    return coin_list

@app.route("/price")
def price():
    """Search for name/symbol of coin to view price/market data"""

    # How to use right now: localhost:5001/price?search=<VALID COIN ID>

    search = request.args.get('search')

    # TODO: add some search validation to make sure each ID
    # TODO: add validation for multiple coins per search (comparison?)

    response = requests.get(f"https://api.coingecko.com/api/v3/simple/price",
                            params={
                                "vs_currencies":"usd",
                                "ids":search,
                                "include_market_cap":"true",
                                "include_24hr_vol":"true",
                                "include_24hr_change":"true",
                                "include_last_updated_at":"true",
                                "x_cg_demo_api_key":COIN_GECKO_KEY
                            },
                            headers={"accept": "application/json"})

    return response.json()


@app.route("/trends")
def trends():
    """Market trends"""

    # How to use right now: localhost:5001/trends?id=<VALID COIN ID>

    # TODO: not sure about which coingecko api endpoint to use for this.
    # TODO: input for from-to dates (datetime in s?)
    # TODO: cryptocurrency id validation via database table

    id = request.args.get('id')

    response = requests.get(f"https://api.coingecko.com/api/v3/coins/markets",
                            params={
                                "vs_currency":"usd",
                                "ids":id,
                                "sparkline":"true",
                                "x_cg_demo_api_key":COIN_GECKO_KEY
                            },
                            headers={"accept": "application/json"})

    return response.text


@app.route('/historical-price-chart', methods=['GET'])
def historical_price_chart():
    """Query historical data api"""

    # How to use right now: localhost:5001/historical-price-chart?id=<VALID COIN ID>&days=<# OF DAYS>

    # TODO: input for from-to dates (datetime in s?)
    # TODO: cryptocurrency id validation via database table

    id = request.args.get('id')
    num_days = request.args.get('days', 7)  # Default to 7 days if 'days' parameter is not provided
    # Validate or parse days, and ensure it’s a positive integer
    try:
        num_days = int(num_days)
        if num_days <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "The 'days' parameter must be a positive integer"}), 400
    today_time = datetime.date.today()
    from_time = today_time - datetime.timedelta(days=num_days)
    today_UNIX = time.mktime(today_time.timetuple())
    from_UNIX = time.mktime(from_time.timetuple())
    # Query CoinGecko API
    try:
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{id}/market_chart/range",
            params={
                "vs_currency": "usd",
                "from": from_UNIX,
                "to": today_UNIX,
                "x_cg_demo_api_key": COIN_GECKO_KEY
            },
            headers={"accept": "application/json"}
        )
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": "Unable to fetch data from CoinGecko"}), 500

    try:
        prices = response.json().get("prices", [])
        chart_data = [{"x": price[0], "y": price[1]} for price in prices]
    except (ValueError, KeyError) as e:
        return jsonify({"error": "Error processing data"}), 500
    
    return jsonify(chart_data), 200

@app.route("/news")
def news():
    """Query news api"""

    # How to use right now: localhost:5001/news?search=<VALID COIN ID>

    # TODO: how are we deciding on from and to dates? inputs from user on frontend?
    # datetime conversion?
    # sortby option? check documentation...

    search = request.args.get('search')

    response = requests.get("https://newsapi.org/v2/everything",
                            params={
                                "q":search,
                                # "from":"2024-10-26",
                                # "to":"2024-10-26",
                                "sortBy":"popularity",
                                "apiKey":NEWS_KEY
                            },
                            headers={"accept": "application/json"})

    return response.text

# TODO: populate database
# TODO: account crud
# TODO: portfolio crud and summation
# dummy values
ACCOUNT = {"username":"aaaaa", "wallet": "bitcoin"}

@app.route("/account")
def account():
    """Account management"""

    # How to use right now: localhost:5001/account

    return ACCOUNT["username"]

@app.route("/portfolio")
def portfolio():
    """Portfolio management"""

    # How to use right now: localhost:5001/portfolio

    return ACCOUNT["wallet"]

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)