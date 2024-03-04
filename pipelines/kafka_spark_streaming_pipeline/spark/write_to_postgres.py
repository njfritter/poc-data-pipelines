import os
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, inline, to_timestamp, to_utc_timestamp
from pyspark.sql import functions as F # Doing this separately to avoid confusion with built in Python functions count, count_if, mean, sum
from pyspark.streaming import StreamingContext

# Set Kafka attributes
raw_kafka_topic = os.environ.get('RAW_TRADES_KAFKA_TOPIC')
agg_kafka_topic = os.environ.get('AGG_TRADES_KAFKA_TOPIC')
kafka_server = os.environ.get('KAFKA_BROKER')
kafka_topic_schema = "array<struct<api_call_timestamp:string,product_id:string,num_trades:int,num_sell_trades:int,num_buy_trades:int,share_volume:double,avg_share_price:double>>"

# Set Postgres attributes
pg_db_name = os.environ.get('POSTGRES_DB_NAME')
pg_db_user = os.environ.get('POSTGRES_DB_USER')
pg_db_pass = os.environ.get('POSTGRES_DB_PASS')
pg_db_host = os.environ.get('POSTGRES_DB_HOST')
pg_db_port = os.environ.get('POSTGRES_DB_PORT')
pg_db_raw_table = os.environ.get('POSTGRES_DB_TRADES_RAW_TABLE')
pg_db_agg_table = os.environ.get('POSTGRES_DB_TRADES_AGG_TABLE')
pg_url = "jdbc:postgresql://" + pg_db_host + ":" + pg_db_port + "/" + pg_db_name


def write_streaming_df_to_postgres(target_table_name) -> None:
    def _execute(df, batch_id):

        df.write \
        .format("jdbc") \
        .mode("append") \
        .option("url", pg_url) \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", target_table_name) \
        .option("user", pg_db_user) \
        .option("password", pg_db_pass) \
        .save()
    
    return _execute


# Write aggregated data from Kafka topic to Postgres
# NOTE: Requires downloading most recent Postgresql Spark Jar from https://jdbc.postgresql.org/download/
# Most recent one was https://jdbc.postgresql.org/download/postgresql-42.7.2.jar
# Change below reference (and `spark-submit` command) as needed

spark = SparkSession \
    .builder \
    .config("spark.sql.shuffle.partitions","2") \
    .config("spark.jars", "./postgresql-42.7.2.jar") \
    .appName("WriteAggCoinbaseTradesDatatoPostgres") \
    .getOrCreate()    


agg_data_stream = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", agg_kafka_topic) \
    .option("includeHeaders", "true") \
    .option("failOnDataLoss", "false") \
    .load()

# TODO: Figure out why below code works + try and use alternative code that more explicitly converts timestamps
exploded_agg_data = agg_data_stream \
    .selectExpr(
        "inline(from_json(CAST(value AS string), '{schema}'))".format(schema=kafka_topic_schema)
    ) \
    .selectExpr("to_utc_timestamp(to_timestamp(api_call_timestamp, \"yyyy-MM-dd'T'HH:mm:ss.SSSXXX\"),'PST') AS api_call_timestamp_utc",
                "to_timestamp(api_call_timestamp, \"yyyy-MM-dd'T'HH:mm:ss.SSSXXX\") AS api_call_timestamp_local",
                "product_id", 
                "num_trades", 
                "num_sell_trades", 
                "num_buy_trades", 
                "share_volume", 
                "avg_share_price") \
    .writeStream \
    .foreachBatch(write_streaming_df_to_postgres(pg_db_agg_table)) \
    .start() \
    .awaitTermination()