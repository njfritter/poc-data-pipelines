# Kafka-Spark Proof of Concept (POC) Data Pipeline: Lambda Architecture

Here, I will be exploring the following streaming data technology use case: building a "lambda architecture".

According to [Wikipedia](https://en.wikipedia.org/wiki/Lambda_architecture):
```
Lambda architecture is a data-processing architecture designed to handle massive quantities of data by taking advantage of both batch and stream-processing methods. This approach to architecture attempts to balance latency, throughput, and fault-tolerance by using batch processing to provide comprehensive and accurate views of batch data, while simultaneously using real-time stream processing to provide views of online data. The two view outputs may be joined before presentation. The rise of lambda architecture is correlated with the growth of big data, real-time analytics, and the drive to mitigate the latencies of map-reduce.
```

This is a fascinating data architecture combining both batch and streaming methods to provide a holistic, up to date picture of data to end users. Recent data can be provided immediately by the streaming layer, while also being corrected by the batch layer as the streaming data gets older and new data is constantly being processed by the streaming layer.

Some other useful links:
- [Snowflake Guide to Lambda Architecture](https://www.snowflake.com/guides/lambda-architecture)
- [Databricks Guide to Lambda Architecture](https://databricks.com/glossary/lambda-architecture)
- [Structured Spark Streaming + Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)

## "Business Need/Use Case"

The company I work for, a holistic financial wellness technology company named FinSolutionsInc, has recently developed a partnership with Coinbase in order to provide its users accessbility to the crypto market and begin to increase their product offerings.

The product manager leading this partnership has requested a POC Crypto data interface for users with the following requirements:
- Show users real time crypto data (number of sell/buy trades, average price, etc) down to the second
- Be able to look back in time at older data
- Provide accurate data to users with a freshness lag of 30 minutes

The product manager also has a long term vision of provide recommendations to users (i.e. buy/sell/hold certain cryptocurrency) based on certain real time factors like recent volume, recent price changes, etc.

### Data Used

For this pipeline, I will be using Coinbase's API to retrieve market data in real time. After much trial and error, I ended up followed these instructions [here](https://docs.cloud.coinbase.com/advanced-trade-api/docs/auth#legacy-api-keys) to successfully query Coinbase's API.

The two Advanced Trading API endpoints I am using are:
- [Get Market Trades](https://docs.cloud.coinbase.com/advanced-trade-api/reference/retailbrokerageapi_getmarkettrades)
- [List All Products](https://docs.cloud.coinbase.com/advanced-trade-api/reference/retailbrokerageapi_getproducts)

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
- Download the most recent Postgresql Spark Jar from https://jdbc.postgresql.org/download/ and save to the `spark` subdirectory
- Update the `pipelines/kafka_spark_streaming_pipeline/set_local_credentials.sh` file with the above Coinbase API key and secret key as well as the relevant Postgres information
- Start the Docker daemon and make sure it is running
- From the base of this repo, run the following commands on a terminal to get Kafka up and running:
    - `cd pipelines/kafka_spark_streaming_pipeline && bash setup_mac.sh`
    - `cd kafka && docker compose -f zk-single-kafka-single.yml up`
        - **NOTE: Let this command run for a few minutes before going onto the next step**
- In a second terminal, navigate again to the base of this repo and run the following commands to set up the Kafka CLI tool and required Python packages:
    - `cd pipelines/kafka_spark_streaming_pipeline && source set_local_credentials.sh`
- Run the data producer script in the second terminal
    - `source venv/bin/activate`
    - `cd kafka && python3 coinbase_data_producer.py trades`
        - *Note: the above Python script accepts a trading pair as an additional argument but defaults to "BTC-USD" if none is provided (like above)*
            - Run `python3 coinbase_data_producer.py -h` for additional usage info
            - TODO: Add functionality to query API and provide valid trading pair values for users
    - You should now see data being queried from the Coinbase API and sent to the Kafka topic!
- In a third terminal, navigate again to the base of this repo and run the following commands to parse the Kafka topic using Spark structured streaming:
    - `cd pipelines/kafka_spark_streaming_pipeline`
    - `source venv/bin/activate`
    - `cd spark && spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_process_trade_stream.py`
    - You should now see Coinbase trading data appear as a dataframe!
- In yet ANOTHER terminal, navigate again to the base of this repo and run the following commands to write the data from Kafka to Postgres:
    - `cd pipelines/kafka_spark_streaming_pipeline && source set_local_credentials.sh`
    - `source venv/bin/activate`
    - `cd spark && spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 --jars ./postgresql-42.7.2.jar write_to_postgres.py`

### Option 2: AWS Environment Setup

STILL TO DO