# App
An example app combining the ImageClassifier and UnifiedAPI sub-packages.

## Design & Instructions
This is designed to mimic both client and server sides of a machine learning service. Presently, this will only allow 
the fashion MNIST dataset to be used. The client will send images from the test set to the server via the message 
broker, which will then be consumed by the server and predictions returned to the message broker. The client will 
consume the returned messages in the background, and mock their storage (e.g. to a database) by printing them to the 
terminal.

To accomplish this, two top-level scripts should be run on separate terminals:

### Client
The `client.py` script can be run directly using the default broker (Pub/Sub) or with the additional `broker` argument.
Therefore to send and receive messages via Kafka:

````commandline
$ python client.py --broker kafka
````

Once running, the client will send requests and listen in the background for responses, printing them as they arrive
from the model server. Messages are sent with a unique identifier (not time stamped), so that messages received from 
the model can be matched to a particular request.

### Predictor (Server)
The `predictor.py` script can be run identically to `client.py` with the additional optional argument `model`, which 
is the name of a saved model within the `ImageClassifier/saved_models` directory. Example usage:

```commandline
$ python predictor.py -model fashion_mnist_latest --broker pubsub
```

By default, the predictor will use
the latest saved fashion MNIST model (therefore run `trainer.py` first).

## Limitations & Next Steps
At the moment, both client and server use the same argument parsing to select a message broker. However, in reality 
only the client should require this option, with the model consuming all implemented message brokers in parallel. 

As mentioned previously, only the fashion MNIST dataset/model can be used in this example, this should be extended for 
the general case.