import json
import os
import uuid
from UnifiedAPI.settings import PROJECT, TEST_TOPIC, TEST_SUB
from typing import Dict
from abc import ABC, abstractmethod
from concurrent.futures import TimeoutError
from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud.pubsub_v1 import PublisherClient, SubscriberClient, publisher
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.errors import TopicAlreadyExistsError
from kafka.admin import NewTopic
# TODO: Implement wait_for_future which accepts a future object and returns when it is completed. Avoids using things
#  like time.sleep(5)


class MessageBroker(ABC):

    subclasses = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.subclasses.append(cls)

    @property
    @abstractmethod
    def subscriber(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def producer(self):
        raise NotImplementedError

    @abstractmethod
    def create_topic(self, topic):
        raise NotImplementedError

    @abstractmethod
    def delete_topic(self, topic):
        raise NotImplementedError

    @abstractmethod
    def create_subscriber(self, name, topic):
        raise NotImplementedError

    @abstractmethod
    def delete_subscriber(self, name):
        raise NotImplementedError

    @abstractmethod
    def send_message(self, topic, message):
        raise NotImplementedError

    @abstractmethod
    def consume(self, sub_name, callback=print, timeout=10):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def broker_callback(message, nested_callback=print) -> None:
        raise NotImplementedError

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

        # subs = self.subscriber.list_subscriptions(project=f"projects/{self.project}")
        # TODO: Not a great way to do this, but can't assign sub to new topic without deleting (possibly detaching)
        #  first. Above expression makes it difficult to get names, otherwise would use that
        for _ in range(2):
            try:
                self.subscriber.create_subscription(
                    name=sub_path, topic=topic_path, **kwargs
                )
                print(f"Subscription created {name} in {self.project}")
                break
            except AlreadyExists:
                print(f"Subscription {name} already exists in {self.project}")
                self.delete_subscriber(name)

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
        return future

    def consume(self, sub_name, callback=print, timeout: int = None):

        sub_path = self.get_subscriber_path(sub_name)
        future = self.subscriber.subscribe(sub_path, lambda message: self.broker_callback(message, callback))
        print(f"Beginning consumption of subscriber: {sub_name}")

        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        try:
            future.result(timeout=timeout)
        except (TimeoutError, KeyboardInterrupt):
            future.cancel()  # Trigger the shutdown.
            future.result()  # Block until the shutdown is complete.

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

    @staticmethod
    def broker_callback(message, nested_callback=print) -> None:
        decoded_data = MessageBroker.decode_data(message.data)
        nested_callback(decoded_data)
        message.ack()

    def __del__(self):
        try:
            self.subscriber.close()
        except (TypeError, ImportError):
            pass


class KafkaBroker(MessageBroker):

    subscriptions = dict()

    def __init__(self, project=None, host=os.environ["KAFKA_HOST"]):
        self.project = project
        self.host = host

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

    def delete_topic(self, topic: str):
        # TODO: This is breaking the connection, docs say AdminClient is early stages/unstable
        # admin = KafkaAdminClient(bootstrap_servers=[self.host])
        # admin.delete_topics([topic])
        pass

    def create_subscriber(self, name, topic, group="mygroup", **kwargs):

        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[self.host],
            group_id=group,
            client_id=name,
            enable_auto_commit=True,
            **kwargs,
        )

        self.subscriptions[name] = consumer

    def delete_subscriber(self, name):

        if self.subscriptions and name in self.subscriptions.keys():
            self.subscriptions.pop(name)
        else:
            print(f"Subscriber {name} does not exist")

    def consume(self, sub_name, callback=print, timeout: int = None):

        # Using same definition as pubsub timeout: None = block indefinitely, which is the default setting here
        if sub_name in self.subscriptions.keys() and timeout is not None:
            self.subscriptions[sub_name].config['consumer_timeout_ms'] = timeout * 1000

        print(f"Beginning consumption of subscriber: {sub_name}")
        for message in self.subscriptions[sub_name]:
            self.broker_callback(message, callback)

    def send_message(self, topic, message):
        message = self.add_id(message)
        encoded_message = self.encode_data(message)
        future = self.producer.send(topic, value=encoded_message).add_callback(self.send_success(message['id'], topic))
        return future

    @staticmethod
    def broker_callback(message, nested_callback=print) -> None:
        decoded_data = MessageBroker.decode_data(message.value)
        nested_callback(decoded_data)

    def __del__(self):
        try:
            self.producer.close()
        except (TypeError, ImportError):
            pass


def example(broker):

    broker.create_topic(TEST_TOPIC)
    broker.create_subscriber(TEST_SUB, TEST_TOPIC)
    for i in range(10):
        broker.send_message(TEST_TOPIC, {'data': f"{i}"})

    broker.consume(TEST_SUB, timeout=10)
    broker.delete_subscriber(TEST_SUB)
    broker.delete_topic(TEST_TOPIC)


def main():
    for broker in MessageBroker.subclasses:
        print(f"Running example case on {broker.__name__} broker")
        example(broker(project=PROJECT))
        print(f"Finished example")


if __name__ == "__main__":
    main()
