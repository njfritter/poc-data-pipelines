# Kafka-Spark Proof of Concept (POC) Data Pipeline

Here, I will be exploring the following streaming data technology use case: [Structured Spark Streaming + Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html).

Some other useful links:
- https://kafka.apache.org/quickstart
- https://github.com/conduktor/kafka-stack-docker-compose

## Business Need/Use Case

A product manager for a holistic financial technology company has requested a real time Crypto data interface that will be able to show users real time crypto data.

The POC will simply surface the data itself; the long term vision the product manager has for the interface is to provide recommendations to users (i.e. buy/sell/hold certain cryptocurrency) based on certain factors like volume, price changes, etc.

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

### Option 1: Local Environment Setup
- Update the `pipelines/kafka_spark_streaming_pipeline/set_local_coinbase_credentials.sh` file with the above API key and secret key
- From the base of this repo, run the following commands on a terminal to get Kafka up and running:
    - `cd pipelines/kafka_spark_streaming_pipeline && bash docker_setup_mac.sh`
    - `cd kafka && docker compose -f zk-single-kafka-single.yml up`
        - **NOTE: Let this command run for a few minutes before going onto the next step**
- In a second terminal, navigate again to the base of this repo and run the following commands to set up the Kafka CLI tool and required Python packages:
    - `cd pipelines/kafka_spark_streaming_pipeline && bash kafka_python_setup_mac.sh`
    - `source set_local_coinbase_credentials.sh`
- Run the data producer script in the second terminal
    - `source venv/bin/activate`
    - `cd kafka && python3 coinbase_data_producer.py trades`
        - *Note: the above Python script accepts a trading pair as an additional argument but defaults to "BTC-USD" if none is provided (like above)*
            - Run `python3 coinbase_data_producer.py -h` for additional usage info
            - TODO: Add functionality to query API and provide valid trading pair values for users
    - You should now see data being queried from the Coinbase API and sent to the Kafka topic!
- In a third terminal, navigate again to the base of this repo and run the following commands to parse the Kafka topic using Spark structured streaming:
    - `source venv/bin/activate`
    - `cd spark && spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_process_trade_stream.py`
    - You should now see Coinbase trading data appear as a dataframe!

### Option 2: AWS Environment Setup

STILL TO DO