# Script that queries Coinbase's API every x seconds, connects to the Kafka broker and writes the data to Kafka

# Custom code to fix import issues with Kafka Python import from Python3.12 (https://stackoverflow.com/a/77588167)
import sys, types

m = types.ModuleType('kafka.vendor.six.moves', 'Mock module')
setattr(m, 'range', range)
sys.modules['kafka.vendor.six.moves'] = m
# TODO: Remove above code chunk when possible

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError

import argparse
import json
import os
import requests
import sys
import time

# Helper functions
from include.utils.helpers import CoinbaseAdvancedTraderAuth, create_kafka_topics, get_aws_parameter, process_trades_data

sleep_interval = 1 # In seconds

# Define Kafka configurations (#TODO: Add support for querying product endpoint)
raw_trades_topic_name = os.environ.get('RAW_TRADES_KAFKA_TOPIC')
aggregated_trades_topic_name = os.environ.get('AGG_TRADES_KAFKA_TOPIC')
default_kafka_broker = os.environ.get('KAFKA_BROKER')

# TODO: Add configurations for logging

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

    # Check endpoint argument and format attributes accordingly
    url = coinbase_endpoint_dict[args.endpoint]
    if args.endpoint == 'trades':
        url = url.format(product_id=args.tradingpair)
        raw_topic_name = raw_trades_topic_name
        processing_function = process_trades_data
        topics = [raw_topic_name, aggregated_trades_topic_name]
        create_kafka_topics(default_kafka_broker, topics)
    else:
        # Must be 'products' or else script will not run
        #TODO: Implement code to process data from this endpoint
        print('The \'products\' endpoint has not been implemented yet, please use the \'trades\' endpoint. Exiting')
        sys.exit()

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
        try:
            r = requests.get(url, auth=auth)
            processed_data_payload = processing_function(r.text)
            producer.send(topic=raw_topic_name, value=processed_data_payload)
            print("Payload written to topic {topic}".format(topic=raw_topic_name))
        except KafkaTimeoutError as timeout_error:
            print("Failed to write data to Kafka due to the following error:\n", timeout_error)
        except Exception as e:
            print("Failed due to generic exception:\n", e)
        time.sleep(sleep_interval)
