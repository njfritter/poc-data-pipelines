# Import packages
import boto3
import hashlib, hmac
import json
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