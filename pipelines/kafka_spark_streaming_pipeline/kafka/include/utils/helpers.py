# Import packages
import boto3
import hashlib, hmac
import json
from kafka.admin import KafkaAdminClient, NewTopic
from requests.auth import AuthBase
import time
from typing import Optional


class CoinbaseAdvancedTraderAuth(AuthBase):
    '''
    Custom Authentication class for Coinbase Advanced Trader API
    https://docs.cloud.coinbase.com/sign-in-with-coinbase/docs/api-key-authentication#python
    Args:
    * public_key: Public key associated with a working Coinbase API key
    * secret_key: Secret key associated with a working Coinbase API key

    Returns:
    * request: request authenication object that can be used to interact with Coinbase's Advanced Trader API
    '''
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    def __call__(self, request):

        timestamp = str(int(time.time())) # NOTE: This timestamp must be received by the Coinbase API within 30 seconds
        message = timestamp + request.method + request.path_url.split('?')[0] + str(request.body or '')
        signature = hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()

        request.headers.update({
            'CB-ACCESS-SIGN': signature.hex(),
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'accept': 'application/json',
        })

        return request

# TODO: Move into separate "AWS" directory
def get_aws_parameter(name: str, region: str, ssm: Optional[boto3.client] = None) -> str:
    '''
    Retreive a parameter from AWS Systems Manager Parameter Store by supplied name and region
    
    Args:
    * name: Name of parameter to retrieve
    * region: AWS region where the parameter resides
    * ssm: Optional pre-initialized boto3 SSM client object

    Returns:
    * value: Parameter value
    '''

    if ssm is None:
        ssm = boto3.client("ssm", region_name=region)

    response = ssm.get_parameter(Name=name)
    value = response['Parameter']['Value']

    return value

def create_kafka_topic(bootstrap_server: str, topic_name: str, num_partitions: Optional[int] = 1, replication_factor: Optional[int] = 1) -> None:
    """
    Function to create a Kafka topic given the bootstrap_server and the topic name (and some optional arguments)
    Args:
    * bootstrap_server: External IP address of the Kafka topic
    * topic_name: Name of the topic
    * num_partitions: Optional argument for number of kafka partitions
    * replication_factor: Optional argument for kafka replication factor
    """

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_server,
            client_id='kafka_topic_creation_client'
        )

        topic_list = [NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)]
        admin_client.create_topics(new_topics=topic_list, validate_only=False)

        print("Topic {topic_name} created successfully".format(topic_name=topic_name))

    except Exception as e:
        print("Could not create topic {topic_name} due to the following issue".format(topic_name=topic_name), e)

def process_trades_data(data: str) -> str:
    """
    Function to help process trade data into a viable format to be sent to Kafka
    Args:
    * data: raw string data in the form of a dictionary returned from the "market trades" Coinbase API endpoint

    Returns:
    * payload: A cleaned set of data to pass to Kafka
    """

    # Minimal processing here; we want to write to Kafka as quickly as possible (and can use Spark to deduplicate as needed)
    # In order to write to Kafka: remove the "trades" key, convert back to string and encode

    trade_dict = json.loads(data)
    trades = str(trade_dict['trades'])
    payload = trades.encode('utf-8')

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