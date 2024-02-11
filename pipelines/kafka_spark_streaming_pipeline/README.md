# Kafka-Spark Proof of Concept (POC) Data Pipeline

Here, I will be exploring the following streaming data technology use case: [Structured Spark Streaming + Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html).

Some other useful links:
- https://kafka.apache.org/quickstart
- https://github.com/conduktor/kafka-stack-docker-compose

## Business Need/Use Case

A product manager for a holistic financial technology company has requested a real time Crypto data interface that will be able to show users real time crypto data.

The POC will simply surface the data itself; the long term vision for the interface is to provide recommendations to users of 

### Data Used 

For this pipeline, I will be using Coinbase's API to retrieve market data in real time. After much trial and error, I ended up followed these instructions [here](https://docs.cloud.coinbase.com/advanced-trade-api/docs/auth#legacy-api-keys) to successfully query Coinbase's API.

I could have used some Python packages to generate pseudo-real data (like [EventSim](https://github.com/viirya/eventsim)) but figured using a real API and going through the trial and error process would be a valuable learning experience. Although for future pipelines I may just use these to get started quicker and then look into other APIs.

The two Advanced Trading API endpoints I chose to use are:
- [List All Products](https://docs.cloud.coinbase.com/advanced-trade-api/reference/retailbrokerageapi_getproducts)
- [Get Market Trades](https://docs.cloud.coinbase.com/advanced-trade-api/reference/retailbrokerageapi_getmarkettrades)

I chose these because they return the most data, as well as data that can be further manipulated with data tools (i.e. Spark!)

I may toy around with the ["Sign in With Coinbase" endpoints](https://docs.cloud.coinbase.com/sign-in-with-coinbase/docs/welcome) and add functionality to query those endpoints in the future.

Some notes:
- Apparently Coinbase Pro is dead, can only use the Advanced Trading API: https://www.reddit.com/r/CoinBase/comments/187ff0w/comment/kbfwyuu/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- Mapping from old Coinbase Pro API to Advanced Trader API: https://docs.cloud.coinbase.com/advanced-trade-api/docs/rest-api-pro-mapping

## Instructions for Reproducing this Pipeline

### Clone Repo

Clone this repo via whatever method you prefer.

### Make a Coinbase Account
- Create a Coinbase account via instructions [here](https://help.coinbase.com/en-au/coinbase/getting-started/getting-started-with-coinbase/create-a-coinbase-account)
- Create a set of **legacy** API credentials via https://www.coinbase.com/settings/api
    - Make sure to save the API key and secret key after API key generation, you won't be able to get them afterwards

### Option 1: Set Credentials + Environment Locally
- Update the `pipelines/kafka_spark_streaming_pipeline/set_local_coinbase_credentials.sh` file with the above API key and secret key:
    - `export COINBASE_API_KEY=YOUR_API_KEY_HERE`
    - `export COINBASE_SECRET_KEY=YOUR_SECRET_KEY_HERE`
- Run the following command on a terminal (may take a few minutes):
    - `cd kafka && docker compose -f zk-single-kafka-single.yml up`
- In a second terminal, run the following commands:
    - `cd pipelines/kafka_spark_streaming_pipeline`
    - `bash local_environment_setup_mac.sh`
    - `source set_local_coinbase_credentials.sh`
- Run the data producer script in the second terminal
    - (If not already in python virtual environment) `source venv/bin/activate`
    - `python3 coinbase_data_producer.py trades`

You should now see data being queried and sent to the Kafka topic!

### Option 2: Set Credentials + Environment Via AWS

STILL TO DO