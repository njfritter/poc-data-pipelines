# Kafka-Spark Proof of Concept (POC) Data Pipeline

Here, I will be exploring the following streaming data technology use case: [Structured Spark Streaming + Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html).

Some other useful links:
- https://kafka.apache.org/quickstart

I will first test the code on my local machine and include a quickstart script for how to do this, but will also be launching the code in AWS. An architecture diagram will be added to this directory.

I will build on this by adding additional pipeline pieces such as replication to a database, batch data processing, simple visualizations and more.

I will include any lessons learned here as well.

## Data Used

For this pipeline, I will be using Coinbase's API to retrieve market data in real time. After much trial and error, I ended up followed these instructions [here](https://docs.cloud.coinbase.com/advanced-trade-api/docs/auth#legacy-api-keys) to successfully query Coinbase's API.

I could have used some Python packages to generate pseudo-real data (like [EventSim](https://github.com/viirya/eventsim)) but figured using a real API and going through the trial and error process would be a valuable learning experience. Although for future pipelines I may just use these to get started quicker and then look into other APIs.

Some notes:
- Apparently Coinbase Pro is dead, can only use the Advanced Trading API: https://www.reddit.com/r/CoinBase/comments/187ff0w/comment/kbfwyuu/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- Mapping from old Coinbase Pro API to Advanced Trader API: https://docs.cloud.coinbase.com/advanced-trade-api/docs/rest-api-pro-mapping

## Instructions for Reproducing this Pipeline

### Clone Repo

Clone this repo via whatever method you prefer.

### Coinbase Account
- Create a Coinbase account via instructions [here](https://help.coinbase.com/en-au/coinbase/getting-started/getting-started-with-coinbase/create-a-coinbase-account)
- Create a set of **legacy** API credentials via https://www.coinbase.com/settings/api
    - Make sure to save the API key and secret key after API key generation, you won't be able to get them afterwards

### Option 1: Locally
- Using the terminal, store the above API key and secret key in environment variables via the following commands:
    - `export COINBASE_API_KEY=YOUR_API_KEY_HERE`
    - `export COINBASE_SECRET_KEY=YOUR_SECRET_KEY_HERE`

### Option 2: Via AWS
- Create an AWS account if you do not already have one (link [here](https://aws.amazon.com/free/?gclid=Cj0KCQiAzoeuBhDqARIsAMdH14EdcNuB2NOS3QOkWZEBqCkzLxFUl20vP_0uqFXRj_jJufvtpAhS8tUaAmmuEALw_wcB&trk=78b916d7-7c94-4cab-98d9-0ce5e648dd5f&sc_channel=ps&ef_id=Cj0KCQiAzoeuBhDqARIsAMdH14EdcNuB2NOS3QOkWZEBqCkzLxFUl20vP_0uqFXRj_jJufvtpAhS8tUaAmmuEALw_wcB:G:s&s_kwcid=AL!4422!3!432339156162!e!!g!!aws%20sign%20up!9572385111!102212379327&all-free-tier.sort-by=item.additionalFields.SortRank&all-free-tier.sort-order=asc&awsf.Free%20Tier%20Types=*all&awsf.Free%20Tier%20Categories=*all))
- Set up the root user account
    - Set up Multi-Factor Authentication for this account
- Create an IAM user group called `developer` with the following permissions (can be more granular if you wish)
    - "AmazonEC2FullAccess"
    - "AmazonS3FullAccess"
    - "AmazonSSMFullAccess"
- Set up an IAM user for yourself (called something like `nfritter`) and add this user to the `developer` IAM group
    - (Recommended) Set up Multi-Factor Authentication for this account as well
- Using the Root User account, create an access key for the above IAM user (can be found in the user profile in the IAM AWS UI)
    - Like the Coinbase API key and secret key, make sure to save the access key and secret key once created (won't be able to see secret key again)
    - Set up a credentials file in ~/.aws/credentials via the instructions [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#shared-credentials-file)
    - (Recommended) Set up an ~/.aws/config file as well with default configurations like region (instructions [here](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#aws-config-file))
- Navigate to AWS Systems Manager, select "Parameter Store" under "Application Management" and select "Create Parameter"
    - Create a parameter for the API key called `coinbase_legacy_api_key` and supply its value when prompted
    - Create a parameter for the secret key called `coinbase_legacy_secret_key` and supply its value when prompted