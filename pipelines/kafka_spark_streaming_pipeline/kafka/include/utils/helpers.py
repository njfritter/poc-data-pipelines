# Import packages
import boto3
import json
from kafka.admin import KafkaAdminClient, NewTopic
from typing import Optional

from coinbase import jwt_generator
import yaml

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

def create_kafka_topics(bootstrap_server: str, topic_names: list, num_partitions: Optional[int] = 1, replication_factor: Optional[int] = 1) -> None:
    """
    Function to create 1 or more Kafka topics given the bootstrap_server and the topic name(s) (and some optional arguments)
    Args:
    * bootstrap_server: External IP address of the Kafka topic
    * topic_names: List of topic names we want to create
    * num_partitions: Optional argument for number of kafka partitions
    * replication_factor: Optional argument for kafka replication factor
    """

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_server,
            client_id='kafka_topic_creation_client'
        )

        topic_list = []
        for topic_name in topic_names:
            topic_list.append(NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor))
        admin_client.create_topics(new_topics=topic_list, validate_only=False)

        print("Topics {topic_names} created successfully".format(topic_names=topic_names))

    except Exception as e:
        print("Could not create topics {topic_names} due to the following issue".format(topic_names=topic_names), e)

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

def generate_jwt(
        request_method: str,
        request_path: str,
        creds_file: str,
        creds_profile: str
    ) -> str:
    """
    Function to help generate JWT (needs to be refreshed every two minutes)
    Args:
    * request_method: API request method
    * request_path: API path for request
    * creds_file: Absolute path to Coinbase credentials file
    * creds_profile: Profile within Coinbase credentials file with specific credentials

    Returns:
    * token: A generated JWT with the proper accesses
    """
    
    # Get Public and Secret Key for Coinbase API Key (REPLACE BELOW WITH ENVIRONMENT VARIABLES)
    with open(creds_file) as credentials:
        credentials_data = yaml.load(credentials, Loader=yaml.Loader)
        keys = credentials_data[creds_profile]
        api_key = keys['api_key']
        secret_key = keys['secret_key']

    jwt_uri = jwt_generator.format_jwt_uri(request_method, request_path)
    jwt_token = jwt_generator.build_rest_jwt(jwt_uri, api_key, secret_key)

    return jwt_token