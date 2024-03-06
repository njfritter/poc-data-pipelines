import os
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, inline, to_timestamp, to_utc_timestamp
from pyspark.sql import functions as F # Doing this separately to avoid confusion with built in Python functions count, count_if, mean, sum
from pyspark.streaming import StreamingContext

# Kafka attributes
kafka_topic = os.environ.get('RAW_TRADES_KAFKA_TOPIC')
target_kafka_topic = os.environ.get('AGG_TRADES_KAFKA_TOPIC')
kafka_server = os.environ.get('KAFKA_BROKER')

kafka_topic_schema = "array<struct<trade_id:string,product_id:string,price:string,size:string,time:string,side:string,bid:string,ask:string>>"

# Cassandra attributes
# TODO: Implement Cassandra catalog
cass_db_speed_layer_catalog = os.environ.get('CASSANDRA_DB_SPEED_LAYER_CATALOG')
cass_db_speed_layer_keyspace = os.environ.get('CASSANDRA_DB_SPEED_LAYER_KEYSPACE')
cass_db_speed_layer_table = os.environ.get('CASSANDRA_DB_SPEED_LAYER_TABLE')
cass_db_host = os.environ.get('CASSANDRA_DB_HOST')
cass_db_port = os.environ.get('CASSANDRA_DB_PORT')

def write_streaming_df_to_cassandra(df) -> None:
    def _execute(df, batch_id):
        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode('append') \
            .options(table=cass_db_speed_layer_table, keyspace=cass_db_speed_layer_keyspace) \
            .save()

    return _execute

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
    .config("spark.jars", "./spark-cassandra-connector-assembly_2.12-3.5.0.jar") \
    .config("spark.cassandra.connection.host", cass_db_host) \
    .config("spark.cassandra.connection.port", cass_db_port) \
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

aggregated_data = exploded_deduped_data \
    .groupBy("api_call_timestamp","product_id") \
    .agg(
        F.count("trade_id").alias("num_trades"),
        F.count_if(col("side") == "SELL").alias("num_sell_trades"),
        F.count_if(col("side") == "BUY").alias("num_buy_trades"),
        F.sum("size").alias("share_volume"),
        F.mean("price").alias("avg_share_price")
    )

# Write aggregated data to Cassandra
agg_data_stream_df = aggregated_data \
    .selectExpr("to_timestamp(api_call_timestamp, \"yyyy-MM-dd'T'HH:mm:ss.SSSXXX\") AS api_call_timestamp_utc",
                "product_id",
                "num_trades",
                "num_sell_trades",
                "num_buy_trades",
                "share_volume",
                "avg_share_price") \
    .writeStream \
    .foreachBatch(write_streaming_df_to_cassandra(aggregated_data)) \
    .start()

# Write aggregated data to separate Kafka topic
aggregated_data \
    .selectExpr("CAST(NULL AS string) AS key", "CAST(to_json(struct(*)) AS string) AS value") \
    .writeStream \
    .outputMode("append") \
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