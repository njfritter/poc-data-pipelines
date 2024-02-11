# Import packages
import argparse
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
coinbase_endpoint_dict = {
    'products' : coinbase_products_endpoint,
    'trades' : coinbase_market_trades_endpoint
}

if __name__ == "__main__":
    # Grab command line arguments
    parser = argparse.ArgumentParser(description='Simple app that will keep querying the Coinbase Advanced Trader API (using legacy API credentials) at regular intervals (i.e. every 5 seconds).')
    parser.add_argument('endpoint', 
                        type=str,
                        choices=['products', 'trades'],
                        help='Coinbase endpoint we wish to query. At this time, accepts either \"products\" (get available currency pairs) or \"trades\" (get information for a specific trading pair)')
    parser.add_argument('--tradingpair',
                        type=str,
                        default='BTC-USD',
                        help='Optional argument to supply a trading pair if \"trades\" is the inputted endpoint. Default trading pair is \"BTC-USD\"')
    parser.add_argument('-c', '--cloud',
                        action='store_true',
                        help='Optional argument to fetch credentials from AWS for this script. If not used, will fetch credentials locally')
    args = parser.parse_args()

    
    # Grab endpoint
    url = coinbase_endpoint_dict[args.endpoint]
    if args.endpoint == 'trades':
        url = url.format(product_id=args.tradingpair)
    
    # Get Public and Secret Key for Coinbase API Key
    # Make sure either the local or AWS setup has been followed via README (or both)
    if args.cloud:
        # (Possible) TODO: Update process + instructions to use credentials via IAM Identity Center: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html
        print("Setting up credentials via AWS")
        region = 'us-east-2'
        coinbase_api_key = get_aws_parameter('coinbase_legacy_api_key', region=region)
        coinbase_secret_key = get_aws_parameter('coinbase_legacy_secret_key', region=region)
    
    else:
        print("Setting up credentials locally")
        coinbase_api_key = os.environ.get('COINBASE_API_KEY')
        coinbase_secret_key = os.environ.get('COINBASE_SECRET_KEY')

    # Create instance of Coinbase Advanced Trader Authentication object
    auth = CoinbaseAdvancedTraderAuth(coinbase_api_key, coinbase_secret_key)

    # Get Coinbase data
    # TODO: Update to account for 429 Too Many Requests via exponential backoff
    print("Querying Coinbase Advanced Trader API")
    while True:
        r = requests.get(url, auth=auth)
        print('\nData Below:\n')
        print(r.text)
        time.sleep(5)