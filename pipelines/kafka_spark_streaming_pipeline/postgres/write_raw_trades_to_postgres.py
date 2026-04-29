import ast
import os
import sched, time
import datetime
from typing import Optional

# Custom code to fix import issues with Kafka Python import from Python3.12 (https://stackoverflow.com/a/77588167)
import sys, types

m = types.ModuleType('kafka.vendor.six.moves', 'Mock module')
setattr(m, 'range', range)
sys.modules['kafka.vendor.six.moves'] = m
# TODO: Remove above code chunk when possible

from kafka import KafkaConsumer
import pandas as pd
import psycopg2

# Set Kafka attributes
raw_kafka_topic = os.environ.get('RAW_TRADES_KAFKA_TOPIC')
kafka_server = os.environ.get('KAFKA_BROKER')

# Set Postgres attributes
pg_db_name = os.environ.get('POSTGRES_DB_NAME')
pg_db_user = os.environ.get('POSTGRES_DB_USER')
pg_db_pass = os.environ.get('POSTGRES_DB_PASS')
pg_db_host = os.environ.get('POSTGRES_DB_HOST')
pg_db_port = os.environ.get('POSTGRES_DB_PORT')
pg_db_raw_trade_table = os.environ.get('POSTGRES_DB_TRADES_RAW_TABLE')
conn = psycopg2.connect(dbname=pg_db_name,
                        host=pg_db_host,
                        port=pg_db_port,
                        user=pg_db_user,
                        password=pg_db_pass)

# Set pandas attributes
raw_table_columns = ['trade_id', 'product_id', 'price', 'size', 'time', 'side', 'bid', 'ask', 'api_call_timestamp']

# Set script attributes
num_polls = 100 # Maximum number of times the KafkaConsumer will poll the Kafka topic
pause_interval = 10


def poll_kafka_topic_iterator(topic: str, broker: str, num_polls: Optional[int] = 10) -> None:
    '''
    Poll Kafka topic using "iterator" method
    Args:
    * topic: Name of Kafka topic to consume from
    * broker: IP address of Kafka broker 
    * num_polls: Optional argument to specify maximum number of times to poll Kafka topic (default is 10)
    '''
    consumer = KafkaConsumer(topic,
                             bootstrap_servers=broker,
                             auto_offset_reset='earliest',
                             group_id='test-poll-group-iterator')

    for _ in range(0, num_polls):
        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            print(message.value.decode('utf-8'))
            print(message.timestamp)
            print('\n\n\n\n\n\n\n\n\n')

def poll_kafka_topic_poll(topic: str, broker: str, num_polls: Optional[int] = 10) -> None:
    '''
    Poll Kafka topic using "poll" method
    Args:
    * topic: Name of Kafka topic to consume from
    * broker: IP address of Kafka broker
    * num_polls: Optional argument to specify maximum number of times to poll Kafka topic (default is 10)
    '''
    consumer = KafkaConsumer(topic,
                             bootstrap_servers=broker,
                             auto_offset_reset='earliest',
                             max_poll_records=50,
                             enable_auto_commit=True,
                             auto_commit_interval_ms=1000,
                             group_id='test-poll-group-poll')


    print('Beginning to poll Kafka queue')
    for _ in range(0, num_polls):
        print('Retrieving records')
        batch_records = consumer.poll(timeout_ms=10000)
        if len(batch_records) == 0:
            print('No records returned, exiting')
            print(batch_records)
            break

        for record in batch_records:
            print(record.value.decode('utf-8'))
            print(record.timestamp)
            print('\n\n\n\n\n\n\n\n\n')

def replicate_raw_trades_to_postgres(topic: str, broker: str, num_polls: int) -> None:
    '''
    Read in raw trade data from Kafka, temporarily convert to a pandas DF and bulk write to a raw table in Postgres using Pandas
    Args:
    * topic: Name of Kafka topic to consume from
    * broker: IP address of Kafka broker
    * num_polls: Number of times the KafkaConsumer polls the Kafka topic
    '''
    consumer = KafkaConsumer(topic,
                             bootstrap_servers=broker,
                             auto_offset_reset='earliest',
                             max_poll_records=500,
                             enable_auto_commit=False,
                             group_id='batch-layer-group')
    
    raw_table_dicts = []

    # Use iterator method for now
    for _ in range(0, num_polls):
        for message in consumer:
            decoded_message = message.value.decode('utf-8')
            api_call_timestamp = datetime.datetime.fromtimestamp(message.timestamp / 1000, datetime.UTC).strftime('%Y-%m-%d %H:%M:%S.%f%z')
            converted_message = ast.literal_eval(decoded_message)
            converted_message_extended = [dict(item, **{'api_call_timestamp': api_call_timestamp}) for item in converted_message]
            raw_table_dicts.extend(converted_message_extended)
            consumer.commit()

    # Temporarily save df to disk so we can do a bulk copy (overwriting any existing files)
    raw_table_df = pd.DataFrame(raw_table_dicts).drop_duplicates(subset='trade_id')
    temp_file = './temp_raw_table_df.csv' 
    raw_table_df.to_csv(temp_file, header=True, index=False, mode='w+')
    f = open(temp_file, 'r+')
    
    cursor = conn.cursor()
    print('\n\nAttempting to write data to Postgres')
    try:
        cursor.copy_expert(sql=f"COPY {pg_db_raw_trade_table} FROM STDIN WITH CSV HEADER DELIMITER as ','", file=f)
        conn.commit()
        print('{0} rows successfully written to Postgres'.format(raw_table_df.shape[0]))
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as e:
        print('The following error occurred: ', e)
        conn.rollback()
        cursor.close()
        return 1
    
if __name__ == "__main__":
    while True:
        replicate_raw_trades_to_postgres(raw_kafka_topic, kafka_server, num_polls)
        print(f"Done attempting write to Postgres, sleeping for {pause_interval} seconds")
        time.sleep(pause_interval)
        #poll_kafka_topic_poll(raw_kafka_topic, kafka_server)
        #poll_kafka_topic_iterator(raw_kafka_topic, kafka_server)