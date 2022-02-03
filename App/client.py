import asyncio
import tensorflow as tf
from UnifiedAPI.adapter import PubsubBroker, KafkaBroker

POST_TOPIC = "client"
PULL_TOPIC = "prediction2"
PROJECT = "vectorassignment"


def receiver(message):

    print(message)


def send_predictions(producer):

    fashion_mnist = tf.keras.datasets.fashion_mnist

    _, (test_images, test_labels) = fashion_mnist.load_data()

    test_images = test_images[10:101]

    for i, e in enumerate(test_images):
        data = {'image': e.tolist()}
        producer.send_message(POST_TOPIC, data)
        # time.sleep(1)


if __name__ == "__main__":

    broker = PubsubBroker(PROJECT)
    # broker = KafkaBroker(PROJECT)
    broker.create_topic(POST_TOPIC)
    broker.create_topic(PULL_TOPIC)
    broker.create_subscriber('pull_client', PULL_TOPIC)
    send_predictions(broker)
    broker.consume('pull_client', timeout=1000)
