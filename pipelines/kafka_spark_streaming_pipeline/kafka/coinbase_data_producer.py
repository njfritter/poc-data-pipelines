# Script that queries Coinbase's API every 5 seconds, connects to the Kafka broker and writes the data to Kafka

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError

import argparse
import ast
import boto3
import json
import os
import requests
import time

# Helper functions
from include.utils.helpers import CoinbaseAdvancedTraderAuth, get_aws_parameter

# Define Kafka configurations
default_trade_topic_name = 'coinbase_trades'
default_product_topic_name = 'coinbase_products'
default_kafka_broker = '127.0.0.1:12345'

# TODO: Add configurations for logging

# Define Coinbase endpoints (there are more, but these return the most interesting data)
coinbase_api_url = "https://api.coinbase.com/api/v3/brokerage/"
coinbase_products_endpoint = coinbase_api_url + "products" # List available currency pairs
coinbase_market_trades_endpoint = coinbase_api_url + "products/{product_id}/ticker" # Requires a trading pair for {product_id}; i.e. 'BTC-USD'
coinbase_endpoint_dict = {
    'products' : coinbase_products_endpoint,
    'trades' : coinbase_market_trades_endpoint
}

def process_trade_data(trade_data: str) -> str:
    """
    Function to help process trade data into a viable format to be sent to Kafka
    Args:
    * trade_data: raw string data in the form of a dictionary returned from the "market trades" Coinbase API endpoint

    Returns:
    * payload: A cleaned set of data to pass to Kafka
    """

    # TODO: Update below to perform more advanced computation
    # For now, we will just grab the first trade and its relevant info
    trade_dict = json.loads(trade_data)
    trades = trade_dict['trades']
    first_trade = trades[0]
    first_trade_dict = {
        "TradingPair":first_trade['product_id'],
        "Price":first_trade['price'],
        "Side":first_trade['side'],
        "ShareAmount":first_trade['size'],
        "TradeDateTime":first_trade['time']
    }
    payload = ("".join(str([first_trade_dict]))).encode('utf-8')
    return payload


def process_products_data(product_data: dict):
    """
    Function to help process products data into a viable format to be sent to Kafka
    Args:
    * product_data: raw data in the form of a dictionary returned from the "products" Coinbase API endpoint
    
    Returns:
    * payload: A cleaned set of data to pass to Kafka
    """
    pass

def fetch_coinbase_data_send_to_kafka(producer, url, topic_name) -> None:
    """
    Function to query Coinbase API, process data (using above functions) and send to Kafka topic
    Args:
    * producer: instance of a kafka producer
    * url: Coinbase URL endpoint 
    * topic_name: Kafka topic to write to

    Returns: None
    """
    pass

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

    # Instantiate a Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=default_kafka_broker
    )

    # Create instance of Coinbase Advanced Trader Authentication object
    auth = CoinbaseAdvancedTraderAuth(coinbase_api_key, coinbase_secret_key)

    # Get Coinbase data
    # TODO: Update to account for 429 Too Many Requests via exponential backoff
    print("Querying Coinbase Advanced Trader API")
    while True:
        # Grab endpoint
        url = coinbase_endpoint_dict[args.endpoint]

        # Make request
        if args.endpoint == 'trades':
            url = url.format(product_id=args.tradingpair)
            r = requests.get(url, auth=auth)
            processed_data_payload = process_trade_data(r.text)
            topic_name = default_trade_topic_name
            producer.send(topic=topic_name, value=processed_data_payload, timestamp_ms=int(time.time()))
            print("Payload written to topic {topic}:".format(topic=topic_name), processed_data_payload)
            time.sleep(5)

        else:
            # TODO: Implement above function to process products data
            continue