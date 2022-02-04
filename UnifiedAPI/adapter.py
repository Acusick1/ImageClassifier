import json
import uuid
from typing import List, Dict
from abc import ABC, abstractmethod
from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud.pubsub_v1 import PublisherClient, SubscriberClient, subscriber, publisher
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.errors import KafkaTimeoutError, TopicAlreadyExistsError
from kafka.admin import NewTopic


def print_callback(message) -> None:
    if isinstance(message, subscriber.message.Message):
        message.ack()

    print(message)


class MessageBroker(ABC):

    @property
    @abstractmethod
    def subscriber(self):
        pass

    @property
    @abstractmethod
    def producer(self):
        pass

    @abstractmethod
    def create_topic(self, topic):
        pass

    @abstractmethod
    def delete_topic(self, topic):
        pass

    @abstractmethod
    def create_subscriber(self, name, topic):
        pass

    @abstractmethod
    def delete_subscriber(self, name):
        pass

    @abstractmethod
    def send_message(self, topic, message):
        pass

    @abstractmethod
    def consume(self, sub_name, callback=print, timeout=10):
        pass

    @staticmethod
    def add_id(message: Dict):

        if 'id' not in message.keys():
            message['id'] = str(uuid.uuid4())

        return message

    @staticmethod
    def encode_data(data):
        return json.dumps(data).encode("utf-8")

    @staticmethod
    def decode_data(data):
        return json.loads(data.decode("utf-8"))

    @staticmethod
    def send_success(message_id, topic):
        print(f"Message id: {message_id} delivered to topic: {topic}")


class PubsubBroker(MessageBroker):

    def __init__(self, project):
        self.project = project

    @property
    def subscriber(self):
        return SubscriberClient()

    @property
    def producer(self):
        return PublisherClient()

    def create_topic(self, topic, **kwargs) -> publisher.futures.Future:

        topic_path = self.get_topic_path(topic)
        response = {}

        try:
            response = self.producer.create_topic(name=topic_path, **kwargs)
            print(f"Created topic {topic} in {self.project}")

        except AlreadyExists:
            print(f"{topic} already exists in {self.project}")

        else:
            print(response)

        return response

    def delete_topic(self, topic):

        topic_path = self.get_topic_path(topic)
        try:
            self.producer.delete_topic(topic=topic_path)
            print(f"Topic: {topic} deleted from project: {self.project}")
        except NotFound:
            print(f"Topic: {topic} does not exist in project: {self.project}")

    def create_subscriber(self, name, topic, **kwargs) -> None:

        sub_path = self.get_subscriber_path(name)
        topic_path = self.get_topic_path(topic)

        try:
            self.subscriber.create_subscription(
                name=sub_path, topic=topic_path, **kwargs
            )
            print(f"Subscription created {name} in {self.project}")

        except AlreadyExists:
            print(f"Subscription {name} already exists in {self.project}")

    def delete_subscriber(self, name) -> None:

        subscription_path = self.get_subscriber_path(name)
        self.subscriber.delete_subscription(subscription=subscription_path)

        print(f"Subscription deleted: {subscription_path}.")

    def send_message(self, topic: str, message: Dict):
        topic_path = self.get_topic_path(topic)
        message = self.add_id(message)
        encoded_message = self.encode_data(message)

        future = self.producer.publish(topic_path, encoded_message)

        if isinstance(future.exception(), NotFound):
            raise NotFound(f"Topic: {topic} not found in project: {self.project}")

        self.send_success(message['id'], topic)

    def consume(self, sub_name, callback=print_callback, timeout=100):

        sub_path = self.get_subscriber_path(sub_name)
        future = self.subscriber.subscribe(sub_path, callback)

        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            future.result(timeout=timeout)
        except TimeoutError:
            future.cancel()  # Trigger the shutdown.
            future.result()  # Block until the shutdown is complete.
        except Exception as e:
            # TODO: Remove once TimeoutError is recognised properly
            print(e)

    def get_topic_path(self, topic):

        topic_name = 'projects/{project_id}/topics/{topic}'.format(
            project_id=self.project,
            topic=topic,
        )

        return topic_name

    def get_subscriber_path(self, subscription_id):

        subscription_name = 'projects/{project_id}/subscriptions/{sub}'.format(
            project_id=self.project,
            sub=subscription_id,
        )

        return subscription_name

    def __del__(self):

        self.subscriber.close()


class KafkaBroker(MessageBroker):

    subscriptions = dict()

    def __init__(self, project=None, host="localhost:9092"):
        self.project = project
        self.host = host

    """
    @property
    def subscriptions(self):
        return dict()

    @subscriptions.setter
    def subscriptions(self, value):
        self.subscriptions.update(value)
    """

    @property
    def subscriber(self):
        return KafkaConsumer(bootstrap_servers=[self.host])

    @property
    def producer(self):
        return KafkaProducer(bootstrap_servers=[self.host])

    @producer.setter
    def producer(self, **kwargs):
        self.producer = KafkaProducer(bootstrap_servers=[self.host], **kwargs)

    def create_topic(self, topic_name: str, num_partitions: int = 1, replication_factor: int = 1):

        new_topic = NewTopic(topic_name, num_partitions, replication_factor)
        admin = KafkaAdminClient(bootstrap_servers=[self.host])
        try:
            test = admin.create_topics([new_topic])
            print(test)
        except TopicAlreadyExistsError:
            print(f"Topic: {topic_name} already exists")

    def delete_topic(self, topic: List):
        admin = KafkaAdminClient(bootstrap_servers=[self.host])
        test = admin.delete_topics(topic)
        print(test)

    def create_subscriber(self, name, topic, **kwargs):

        if self.subscriptions and name in self.subscriptions.keys():
            print('subscriber already exists!')
        else:
            consumer = KafkaConsumer(
                bootstrap_servers=[self.host],
                client_id=name,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                **kwargs,
            )

            consumer.subscribe([topic])
            self.subscriptions[name] = consumer

    def delete_subscriber(self, name):

        if self.subscriptions and name in self.subscriptions.keys():
            self.subscriptions.pop(name)
        else:
            print(f"Subscriber {name} does not exist")

    def consume(self, sub_name, callback=print_callback, timeout=10):

        if sub_name in self.subscriptions.keys():
            self.subscriptions[sub_name].config['consumer_timeout_ms'] = timeout * 1000

        try:
            for message in self.subscriptions[sub_name]:
                decoded_message = self.decode_data(message.value)
                callback(decoded_message)

        except KafkaTimeoutError:
            print('Timed out')

    def send_message(self, topic, message):
        message = self.add_id(message)
        encoded_message = self.encode_data(message)
        result = self.producer.send(topic, value=encoded_message)
        self.send_success(message['id'], topic)

    def __del__(self):

        self.producer.close()


def pubsub_example():
    name = 'test'
    topic = 'testtopic'

    a = PubsubBroker("vectorassignment")
    a.create_topic(topic)
    for i in range(10):
        a.send_message(topic, {'data': f"{i}"})

    a.create_subscriber(name, topic)
    a.consume(name)


def kafka_example():
    name = 'test'
    topic = 'testing'

    a = KafkaBroker("vectorassignment")
    # a.delete_topic([topic])
    for i in range(10):
        a.send_message(topic, {'data': f"{i}"})

    a.create_subscriber(name, topic)
    a.consume(name)


if __name__ == "__main__":

    pubsub_example()
    kafka_example()
