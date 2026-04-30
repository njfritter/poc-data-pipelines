#!/bin/bash
# Set environment variables if not using cloud
export COINBASE_CRED_FILE_PATH=YOUR-FULL-CREDENTIALS-FILE-PATH
export COINBASE_CRED_FILE_PROFILE=YOUR-CREDENTIALS-PROFILE

# Kafka attributes
export RAW_TRADES_KAFKA_TOPIC=coinbase_trades_raw_data
export AGG_TRADES_KAFKA_TOPIC=coinbase_trades_aggregated_metrics
export KAFKA_BROKER=localhost:9092

# Cassandra attributes
export CASSANDRA_DB_CATALOG=NONE
export CASSANDRA_DB_KEYSPACE=kafka_spark_keyspace
export CASSANDRA_DB_SPEED_LAYER_TABLE=speed_layer
export POSTGRES_DB_HOST=127.0.0.1
export POSTGRES_DB_PORT=9042

export POSTGRES_DB_NAME=poc_data_pipelines
export POSTGRES_DB_USER=YOUR-POSTGRES-DB-USER-HERE
export POSTGRES_DB_PASS=YOUR-POSTGRES-DB-PASS-HERE
export POSTGRES_DB_HOST=localhost
export POSTGRES_DB_PORT=5432
export POSTGRES_DB_TRADES_RAW_TABLE=NONE # Not implemented yet
export POSTGRES_DB_TRADES_AGG_TABLE=kafka_spark_streaming_pipeline.speed_layer