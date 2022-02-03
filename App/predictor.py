import os
import numpy as np
import tensorflow as tf
from ImageClassifier import MODEL_DIR
from UnifiedAPI.adapter import PubsubBroker, KafkaBroker

PULL_TOPIC = "client"
POST_TOPIC = "prediction2"
PROJECT = "vectorassignment"


def format_message_data(data):
    img = np.array(data['image'], dtype=np.uint8)
    img = np.expand_dims(img, 0)
    return img


def get_prediction(message):

    img = format_message_data(message)
    probs = model.predict(img)
    probs = np.round(probs, 2)

    result = {name: float(p) for name, p in zip(class_names, probs[0]) if p > 0.05}
    out = {'id': message['id'], 'predictions': result}
    broker.send_message(POST_TOPIC, out)


if __name__ == "__main__":

    model_name = "fashion_mnist_20220203-192147"
    model = tf.keras.models.load_model(os.path.join(MODEL_DIR, model_name))
    class_names = np.array(['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat',
                   'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot'])

    sub_name = 'modelserver'
    broker = PubsubBroker(PROJECT)
    # broker = KafkaBroker(PROJECT)
    broker.create_subscriber(sub_name, PULL_TOPIC)
    broker.consume(sub_name, callback=get_prediction)
