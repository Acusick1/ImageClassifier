# import asyncio
import settings
import tensorflow as tf
from UnifiedAPI import adapter


def receiver(message):

    print(message)


def send_predictions(producer):

    fashion_mnist = tf.keras.datasets.fashion_mnist

    _, (test_images, test_labels) = fashion_mnist.load_data()

    test_images = test_images[10:101]

    for i, e in enumerate(test_images):
        data = {'image': e.tolist()}
        producer.send_message(settings.POST_TOPIC, data)
        # time.sleep(1)


if __name__ == "__main__":

    broker = adapter.PubsubBroker(settings.PROJECT)
    # broker = adapter.KafkaBroker(settings.PROJECT)
    broker.create_topic(settings.POST_TOPIC)
    broker.create_topic(settings.PULL_TOPIC)
    broker.create_subscriber('pull_client', settings.PULL_TOPIC)
    send_predictions(broker)
    broker.consume('pull_client', timeout=1000)
