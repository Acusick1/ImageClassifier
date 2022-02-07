import asyncio
import argparse
import tensorflow as tf
from App.settings import PROJECT, REQUEST_TOPIC, CLIENT_SUB, RETURN_TOPIC
from UnifiedAPI import adapter


async def send_predictions(producer):

    fashion_mnist = tf.keras.datasets.fashion_mnist

    _, (test_images, test_labels) = fashion_mnist.load_data()

    # Sending first 50 images for prediction
    test_images = test_images[:50]

    for i, e in enumerate(test_images):
        data = {'image': e.tolist()}
        producer.send_message(REQUEST_TOPIC, data)
        await asyncio.sleep(1)


async def run(broker):

    await asyncio.gather(
        asyncio.to_thread(broker.consume, CLIENT_SUB),
        send_predictions(broker),
    )


def main():

    parser = argparse.ArgumentParser(
        description="Sending requests to model server and receive response via message broker"
    )

    parser.add_argument("--broker",
                        default="pubsub",
                        choices=["pubsub", "kafka"],
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
    broker.create_subscriber(CLIENT_SUB, RETURN_TOPIC)

    asyncio.run(run(broker))


if __name__ == "__main__":

    main()
