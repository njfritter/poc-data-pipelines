from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode
from pyspark.streaming import StreamingContext

kafka_topic = "coinbase_trades"
kafka_server = "127.0.0.1:12345"

spark = SparkSession \
    .builder \
    .appName("CoinbaseTradesDeduplication") \
    .getOrCreate()

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", kafka_topic) \
    .option("includeHeaders", "true") \
    .load() \
    .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

query = df.writeStream \
    .format("console") \
    .option("truncate","true") \
    .start() \
    .awaitTermination()
