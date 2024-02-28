#!/bin/bash
# Set environment variables if not using cloud
export COINBASE_API_KEY=YOUR-API-KEY-HERE
export COINBASE_SECRET_KEY=YOUR-API-SECRET-HERE

export POSTGRES_DB_NAME=poc_data_pipelines
export POSTGRES_DB_USER=YOUR-POSTGRES-DB-USER-HERE
export POSTGRES_DB_PASS=YOUR-POSTGRES-DB-PASS-HERE
export POSTGRES_DB_HOST=localhost
export POSTGRES_DB_PORT=5432
export POSTGRES_DB_TRADES_RAW_TABLE=NONE # Not implemented yet
export POSTGRES_DB_TRADES_AGG_TABLE=kafka_spark_streaming_pipeline.streaming_layer