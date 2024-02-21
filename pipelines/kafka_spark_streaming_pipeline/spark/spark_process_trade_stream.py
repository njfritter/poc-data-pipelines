import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, inline
from pyspark.sql import functions as F # Doing this separately to avoid confusion with built in Python functions count, count_if, mean, sum
from pyspark.streaming import StreamingContext

kafka_topic = "coinbase_trades_raw_data"
target_kafka_topic = "coinbase_trade_aggregated_metrics"
kafka_server = "127.0.0.1:12345"
kafka_topic_schema = "array<struct<trade_id:string,product_id:string,price:string,size:string,time:string,side:string,bid:string,ask:string>>"

"""
# Example output of data in the Kafka topic we are retrieving; we have to read it in as JSON with a declarative schema
[{'trade_id': '603790709', 'product_id': 'BTC-USD', 'price': '52076.68', 'size': '0.00064681', 'time': '2024-02-16T02:35:40.784239Z', 'side': 'SELL', 'bid': '', 'ask': ''},
{'trade_id': '603790708', 'product_id': 'BTC-USD', 'price': '52073.62', 'size': '0.00009312', 'time': '2024-02-16T02:35:39.787328Z', 'side': 'BUY', 'bid': '', 'ask': ''},
...............
...............
...............
{'trade_id': '603790705', 'product_id': 'BTC-USD', 'price': '52073.51', 'size': '0.05053829', 'time': '2024-02-16T02:35:39.680906Z', 'side': 'BUY', 'bid': '', 'ask': ''},
{'trade_id': '603790704', 'product_id': 'BTC-USD', 'price': '52073.52', 'size': '0.002', 'time': '2024-02-16T02:35:39.680906Z', 'side': 'BUY', 'bid': '', 'ask': ''}]
"""

spark = SparkSession \
    .builder \
    .config("spark.sql.shuffle.partitions","2") \
    .appName("CoinbaseTradesDeduplicationAndAggregation") \
    .getOrCreate()

# Make console output less verbose by setting log level to WARN
spark.sparkContext.setLogLevel("WARN")

# TODO: See if "failOnDataLoss" parameter can be removed (or if there can be a "testing" vs "production" mode where the value is false and true, respectively)
raw_data_stream = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", kafka_topic) \
    .option("includeHeaders", "true") \
    .option("failOnDataLoss", "false") \
    .load()

# Using 1 minute as an conservative estimate for a lookback window so that Spark doesn't have to store all data in state
# https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#streaming-deduplication
exploded_deduped_data = raw_data_stream \
    .selectExpr(
        "timestamp AS api_call_timestamp",
        "inline(from_json(CAST(value AS string), '{schema}'))".format(schema=kafka_topic_schema)
    ) \
    .withWatermark("api_call_timestamp", "1 minute") \
    .dropDuplicates(["trade_id"])

# TODO: See if "exploded_deduped_data" above can be streamed to Postgres and act as the "batch" layer, or written to a new Kafka topic

# TODO: See how "api_call_timestamp" can be added to the below aggregation to create a unique PK (concatenation of product_id and api_call_timestamp)
aggregated_data = exploded_deduped_data \
    .groupBy("product_id") \
    .agg(
        F.count("trade_id").alias("num_trades"),
        F.count_if(col("side") == "SELL").alias("num_sell_trades"),
        F.count_if(col("side") == "BUY").alias("num_buy_trades"),
        F.sum("size").alias("share_volume"),
        F.mean("price").alias("avg_share_price")
    )

# Write aggregated data to separate Kafka topic
aggregated_data \
    .selectExpr("CAST(NULL AS string) AS key", "CAST(to_json(struct(*)) AS string) AS value") \
    .writeStream \
    .outputMode("complete") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("topic", target_kafka_topic) \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .start()

query = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", target_kafka_topic) \
    .option("includeHeaders", "true") \
    .load() \
    .selectExpr("timestamp", "CAST(value AS string)") \
    .writeStream \
    .format("console") \
    .option("truncate","false") \
    .start() \
    .awaitTermination()