import json
from abc import ABC, abstractmethod
from google.api_core.exceptions import AlreadyExists
from google.cloud.pubsub import PublisherClient, SubscriberClient
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaTimeoutError


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
    def encode_data(data):
        return json.dumps(data).encode("utf-8")

    @staticmethod
    def decode_data(data):
        return json.loads(data.decode("utf-8"))


class PubsubBroker(MessageBroker):

    def __init__(self, project):
        self.project = project

    @property
    def subscriber(self):
        return SubscriberClient()

    @property
    def producer(self):
        return PublisherClient()

    def create_topic(self, topic, **kwargs):

        topic_path = self.get_topic_path(topic)

        try:
            response = self.producer.create_topic(name=topic_path, **kwargs)
            print(f"Created topic {topic} in {self.project}")

        except AlreadyExists:
            print(f"{topic} already exists in {self.project}")

        else:
            print(response)

    def delete_topic(self, topic):

        topic_path = self.get_topic_path(topic)
        self.producer.delete_topic(topic=topic_path)

        print(f"Topic {topic} deleted from {self.project} project")

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

    def send_message(self, topic, message):
        topic_path = self.get_topic_path(topic)
        future = self.producer.publish(topic_path, self.encode_data(message))
        print(future.result())

    def consume(self, sub_name, callback=print, timeout=10):

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

    def __init__(self, project, host="localhost:9092"):
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

    def create_topic(self, topic):
        pass

    def delete_topic(self, topic):
        pass

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

    def consume(self, sub_name, callback=print, timeout=10):

        if sub_name in self.subscriptions.keys():
            self.subscriptions[sub_name].config['consumer_timeout_ms'] = timeout * 1000

        try:
            for message in self.subscriptions[sub_name]:
                decoded_message = self.decode_data(message.value)
                callback(decoded_message)

        except KafkaTimeoutError:
            print('Timed out')

    def send_message(self, topic, message):
        encoded_message = self.encode_data(message)
        result = self.producer.send(topic, value=encoded_message)
        print(result)

    def __del__(self):

        self.producer.close()


def pubsub_example():
    name = 'test'
    topic = 'testtopic'

    a = PubsubBroker("vectorassignment")
    for i in range(10):
        a.send_message(topic, f"{i}")

    a.create_subscriber(name, topic)
    a.consume(name)


def kafka_example():
    name = 'test'
    topic = 'testtopic'

    a = KafkaBroker("vectorassignment")
    for i in range(10):
        a.send_message(topic, f"{i}")

    a.create_subscriber(name, topic)
    a.consume(name)


if __name__ == "__main__":

    pubsub_example()
    kafka_example()
