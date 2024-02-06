# Simple app that will keep querying the Coinbase Advanced Trader API (using legacy API credentials) at regular intervals (i.e. every 5 seconds)
# TODO: Update this to be able to accept command line arguments for the endpoint we wish to query (this way it can be run on multiple AWS instances/processes to gather even more data)

# Import packages
import boto3
import os
import requests
import time

# Import helper functions
from include.utils.helpers import CoinbaseAdvancedTraderAuth, get_aws_parameter

# Define Coinbase endpoints (there are more, but these return the most interesting data)
coinbase_api_url = "https://api.coinbase.com/api/v3/brokerage/"
coinbase_products_endpoint = coinbase_api_url + "products" # List available currency pairs
coinbase_market_trades_endpoint = coinbase_api_url + "products/{product_id}/ticker" # Requires a trading pair for {product_id}; i.e. 'BTC-USD'

# Define boolean for determining whether to load credentials locally (False) or via AWS (True)
prod = False

# Choose URL we will be retrieving data from
url = coinbase_products_endpoint

if __name__ == "__main__": 
    print("Querying Coinbase Advanced Trader API")
    # Get Public and Secret Key for Coinbase API Key (REPLACE BELOW WITH ENVIRONMENT VARIABLES)
    if not prod:
        # Make sure to set these values beforehand via
        # `export COINBASE_API_KEY=YOUR_API_KEY_HERE`
        # `export COINBASE_SECRET_KEY=YOUR_SECRET_KEY_HERE`
        # TODO: Add the above to start up instructions
        coinbase_api_key = os.environ.get('COINBASE_API_KEY')
        coinbase_secret_key = os.environ.get('COINBASE_SECRET_KEY')
    
    else:
        coinbase_api_key = get_aws_parameter('coinbase_legacy_api_key')
        coinbase_secret_key = get_aws_parameter('coinbase_legacy_secret_key')


    # Create instance of Coinbase Advanced Trader Authentication object
    auth = CoinbaseAdvancedTraderAuth(coinbase_api_key, coinbase_secret_key)

    # Get Coinbase data
    # TODO: Update to account for 429 Too Many Requests via exponential backoff
    while True:
        r = requests.get(url, auth=auth)
        print('\nData Below:\n')
        print(r.text)
        time.sleep(5)