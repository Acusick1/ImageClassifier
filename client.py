import asyncio
import argparse
import tensorflow as tf
from App.settings import PROJECT, REQUEST_TOPIC, CLIENT_SUB, RETURN_TOPIC
from UnifiedAPI import adapter
from UnifiedAPI.settings import BROKERS


async def send_predictions(broker: adapter.MessageBroker) -> None:
    """
    Send request (image) to message broker topic to be consumed by model server
    :param broker: MessageBroker concrete class used to send messages
    :return: None, broker will print id of sent messages
    """
    fashion_mnist = tf.keras.datasets.fashion_mnist

    _, (test_images, test_labels) = fashion_mnist.load_data()

    # Sending first 50 images for prediction
    test_images = test_images[:50]

    for i, e in enumerate(test_images):
        data = {'image': e.tolist()}
        broker.send_message(REQUEST_TOPIC, data)
        await asyncio.sleep(1)


async def run(broker: adapter.MessageBroker) -> None:
    """
    Asynchronous wrapper sending requests to model server and processing responses as they return
    :param broker: MessageBroker concrete class to send and consume messages
    :return: None
    """
    await asyncio.gather(
        asyncio.to_thread(broker.consume, CLIENT_SUB),
        send_predictions(broker),
    )


def main():
    """
    Mimicking client by sending test data to model server, while simultaneously consuming responses
    """

    parser = argparse.ArgumentParser(
        description="Sending requests to model server and receive response via message broker"
    )

    parser.add_argument("--broker",
                        default=BROKERS[0],
                        choices=BROKERS,
                        help=f"Broker to send messages",
                        )

    args = parser.parse_args()

    if args.broker == "pubsub":
        broker = adapter.PubsubBroker(PROJECT)
    elif args.broker == "kafka":
        broker = adapter.KafkaBroker(PROJECT)
    else:
        raise ValueError

    # Ensure topic is created (if predictor not yet run)
    broker.create_topic(RETURN_TOPIC)
    # Create subscriber to receive model predictions
    broker.create_subscriber(CLIENT_SUB, RETURN_TOPIC)

    asyncio.run(run(broker))


if __name__ == "__main__":

    main()
