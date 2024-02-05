# Kafka-Spark Proof of Concept (POC) Data Pipeline

Here, I will be exploring the following streaming data technology use case: [Structured Spark Streaming + Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html).

Some other useful links:
- https://kafka.apache.org/quickstart

I will first test the code on my local machine and include a quickstart script for how to do this, but will also be launching the code in AWS. An architecture diagram will be added to this directory.

I will build on this by adding additional pipeline pieces such as replication to a database, batch data processing, simple visualizations and more.

I will include any lessons learned here as well.

## Data Used

For this pipeline, I will be using Coinbase's API to retrieve market data in real time. After much trial and error, followed these instructions [here](https://docs.cloud.coinbase.com/advanced-trade-api/docs/auth#legacy-api-keys) to successfully query Coinbase's API.

I could have used some Python packages to generate pseudo-real data (like [EventSim](https://github.com/viirya/eventsim)) but figured using a real API and going through the trial and error process would be a valuable learning experience. Although for future pipelines I may just use these to get started quicker and then look into other APIs.

Some notes:
- Apparently Coinbase Pro is dead, can only use the Advanced Trading API: https://www.reddit.com/r/CoinBase/comments/187ff0w/comment/kbfwyuu/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
- Mapping from old Coinbase Pro API to Advanced Trader API: https://docs.cloud.coinbase.com/advanced-trade-api/docs/rest-api-pro-mapping