import argparse
import pathlib
import numpy as np
import tensorflow as tf
from ImageClassifier.settings import MODEL_DIR, DEFAULT_MNIST_MODEL
from App.settings import PROJECT, REQUEST_TOPIC, RETURN_TOPIC, MODEL_SUB, CLIENT_SUB
from UnifiedAPI import adapter
# TODO: Load latest version of given model
# TODO: Load and parse class names


def format_message_data(data):
    img = np.array(data['image'], dtype=np.uint8)
    img = np.expand_dims(img, 0)
    return img


def get_prediction(message, broker):

    img = format_message_data(message)
    probs = model.predict(img)
    probs = np.round(probs, 2)

    result = {name: float(p) for name, p in zip(class_names, probs[0]) if p > 0.05}
    out = {'id': message['id'], 'predictions': result}
    broker.send_message(RETURN_TOPIC, out)


def main():
    # TODO: This should run all available brokers, consuming them in parallel/asynchronously
    pass


if __name__ == "__main__":

    class_names = np.array(['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
                            'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot'])

    parser = argparse.ArgumentParser(
        description="Using a saved tensorflow model to predict and return client requests"
    )

    parser.add_argument("-model",
                        default=DEFAULT_MNIST_MODEL,
                        help=f"Name of trained model directory within {MODEL_DIR}"
                        )

    parser.add_argument("--broker",
                        default="pubsub",
                        choices=["pubsub", "kafka"],
                        help=f"Broker to send messages",
                        )

    args = parser.parse_args()

    model_path = pathlib.Path(MODEL_DIR, args.model)
    if not pathlib.Path.is_dir(model_path):
        raise NotADirectoryError(f"Model {args.model} not found in {MODEL_DIR}")

    model = tf.keras.models.load_model(model_path)

    if args.broker == "pubsub":
        broker = adapter.PubsubBroker(PROJECT)
    elif args.broker == "kafka":
        broker = adapter.KafkaBroker(PROJECT)
    else:
        raise ValueError

    # Setting up client request topic and model subscriber
    broker.create_topic(REQUEST_TOPIC)
    broker.create_subscriber(MODEL_SUB, REQUEST_TOPIC)

    # Setting up model prediction topic and client subscriber
    broker.create_topic(RETURN_TOPIC)
    broker.create_subscriber(CLIENT_SUB, RETURN_TOPIC)

    # No timeout set, will block indefinitely
    broker.consume(MODEL_SUB, callback=lambda message: get_prediction(message, broker))
