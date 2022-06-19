# Client-Server Image Classifier

This repository mimics a client interaction with a server based machine learning service. Models are trained, saved and served to classify incoming images from a client machine. This interaction is carried out in a robust fashion using a choice of two message brokers: Apache Kafka and Google Pub/Sub.

---
## Modules
The repository is separated into 3 sub-modules:
### ImageClassifier
A simple multi-class CNN trainer using TensorFlow.
### UnifiedAPI
A unified message broker API, allowing both Google Pub/Sub and Apache Kafka to be used.
### App
An example app combining both the ImageClassifier and Unified API to mimic client requests (images) and model server responses (predictions).

---

Individual README files are located within each sub-package directory.
## Installation

The package has been made using [Poetry](https://python-poetry.org/), and can be installed via:

```commandline
$ git clone https://github.com/Acusick1/ImageClassifier
$ cd ImageClassifier
$ pip -m install .
```

## Message Brokers
The message brokers used require some additional setup.

### Google Pub/Sub
This project uses the Pub/Sub client library. A project and service account with the necessary project permissions are required, please follow the instructions in the [documentation](https://cloud.google.com/pubsub/docs/quickstarts).

Authentication requires the environment variable below to be set:
`GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account_key.json`

Finally, the `PROJECT` variable in `UnifiedAPI/settings.py` must be set to Pub/Sub project identifier that you created.

### Apache Kafka
Follow the quickstart [instructions](https://kafka.apache.org/quickstart) to install Apache Kafka.

It is assumed you are running Kafka on `localhost:9092`. If this is not the case, change the `KAFKA_HOST` variable in `UnifiedAPI/settings.py` to the required Kafka server.

### Testing
To validate the installation and message broker setup, run the test cases from the top level directory:

```commandline
$ python -m unittest
```