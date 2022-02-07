# Unified API

Message broker API, allowing Google Pub/Sub and Apache Kafka to be used interchangeably.

This is a first attempt at an adapter to send and receive messages from both brokers, using consistent methods from 
the blueprint class. It is working for the use cases in this project, however it leaves a lot to be desired in terms 
of functionality and publisher best practices. Some of this is due to the limited functionality of the Kafka client 
used, which will likely be need to be changed to allow functionality equivalent to the Pub/Sub client.

There is no top-level script for this module, however the main function within `UnifiedAPI/adapter.py` can be run to 
show an example of each broker sending and consuming messages.

## Next Steps

- Look into changing Kafka client library, much of the core Kafka (and equivalent Pub/Sub) capability is either not 
there or unstable
- Refactor adapter when this is fixed, some Pub/Sub functionality is poorly used to match it with Kafka client
- Implement additional functionality (detach subscriptions, different pulling methods, batching, partitioning)
- Tests are only system based currently, use mocking for unit tests and provide as much coverage as possible