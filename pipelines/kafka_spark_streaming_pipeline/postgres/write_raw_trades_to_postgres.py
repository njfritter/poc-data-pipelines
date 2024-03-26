import ast
import os
import sched, time

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
raw_table_columns = ['trade_id', 'product_id', 'price', 'size', 'time', 'side', 'bid', 'ask']

# Set script attributes
batch_size = 50
pause_interval = 10


def poll_kafka_topic(topic: str, broker: str) -> None:
    '''
    Read in raw trade data from Kafka and write to a raw table in Postgres
    Args:
    * topic: Name of Kafka topic to consume from
    * broker: IP address of Kafka broker 
    '''
    while True:
        consumer = KafkaConsumer(topic,
                        bootstrap_servers=broker,
                        auto_offset_reset='earliest',
                        group_id='test-poll-group')

        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            print(message.value.decode('utf-8'))
            print('\n\n\n\n\n\n\n\n\n')

def replicate_raw_trades_to_postgres(topic: str, broker: str, batch_size: int) -> None:
    '''
    Read in raw trade data from Kafka, temporarily convert to a pandas DF and bulk write to a raw table in Postgres using Pandas
    Args:
    * topic: Name of Kafka topic to consume from
    * broker: IP address of Kafka broker
    * batch_size: Number of messages to read from Kafka before writing to Postgres
    '''
    consumer = KafkaConsumer(topic,
                             bootstrap_servers=broker,
                             auto_offset_reset='earliest',
                             group_id='batch-layer-group')
    
    i = 0
    raw_table_dicts = []
    # TODO: Figure out how to get api_call_timestamp and add to below payload
    for message in consumer:
        if i < batch_size:
            decoded_message = message.value.decode('utf-8')
            converted_message = ast.literal_eval(decoded_message)
            raw_table_dicts.extend(converted_message)
            i += 1
        else:
            break

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
        replicate_raw_trades_to_postgres(raw_kafka_topic, kafka_server, batch_size)
        print(f"Done attempting write to Postgres, sleeping for {pause_interval} seconds")
        time.sleep(pause_interval)