from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, inline
from pyspark.sql import functions as F # Doing this separately to avoid confusion with built in Python functions count, count_if, mean, sum
from pyspark.streaming import StreamingContext

kafka_topic = "coinbase_trades"
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
    .appName("CoinbaseTradesDeduplication") \
    .getOrCreate()

# Make console output less verbose by setting log level to WARN
spark.sparkContext.setLogLevel("WARN")


df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", kafka_topic) \
    .option("includeHeaders", "true") \
    .load() \
    .selectExpr(
        "timestamp AS api_call_timestamp",
        "inline(from_json(CAST(value AS string), '{schema}'))".format(schema=kafka_topic_schema)
    )

# Using 1 minute as an conservative estimate for a lookback window so that Spark doesn't have to store all data in state
# https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#streaming-deduplication
deduped_df = df \
    .withWatermark("api_call_timestamp", "1 minute") \
    .dropDuplicates(["trade_id"])

aggregated_df = deduped_df \
    .groupBy("product_id") \
    .agg(
        F.count("trade_id").alias("Number of Trades"),
        F.count_if(col("side") == "SELL").alias("Number of Sell Trades"),
        F.count_if(col("side") == "BUY").alias("Number of Buy Trades"),
        F.sum("size").alias("Share Volume"),
        F.mean("price").alias("Average Share Price")
    )

query = aggregated_df \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .option("truncate","true") \
    .start() \
    .awaitTermination()
