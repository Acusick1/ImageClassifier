from os import environ as env

PROJECT = "vectorassignment"
TEST_TOPIC = "test_topic"
TEST_SUB = "test_sub"
BROKERS = ["pubsub", "kafka"]

try:
    KAFKA_HOST = env["KAFKA_HOST"]
except KeyError:
    env["KAFKA_HOST"] = "localhost:29092"
