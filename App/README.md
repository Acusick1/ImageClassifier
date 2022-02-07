# (In progress)
# App
An example app combining the ImageClassifier and UnifiedAPI sub-packages.

## Design
This is designed to mimic both client and server sides of a machine learning service. Presently, this will only allow 
the fashion MNIST dataset to be used. The client will send images from the test set to the server via the message 
broker, which will then be consumed by the server and predictions returned to the message broker. The client will 
consume the returned messages in the background, and mock their storage (e.g. to a database) by printing them to the 
terminal.

To accomplish this, two top-level scripts should be run on separate terminals:

### Client

### Predictor (Server)


### Limitations
At the moment, both client and server use the same argument parsing to select a message broker. However, in reality 
only the client should require this option, with the model consuming all implemented message brokers in parallel. 

As mentioned previously, only the fashion MNIST dataset/model can be used in this example, this should be extended for 
the general case.

## Instructions

## Next Steps