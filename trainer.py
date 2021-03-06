import os
import pathlib
import argparse
import tensorflow as tf
import tensorflow_datasets as tfds
import numpy as np
from ImageClassifier.settings import MODEL_DIR, DATASET_DIR, IMG_WIDTH, IMG_HEIGHT, BATCH_SIZE, EXAMPLE_TF_DATASET
from datetime import datetime


def create_model(num_classes: int) -> tf.keras.Sequential:

    model = tf.keras.Sequential([
        # TODO: Remove rescaling from model, use in data preparation phase
        tf.keras.layers.Rescaling(1./255),  # Normalising image to max of 1
        tf.keras.layers.Conv2D(filters=32, kernel_size=3, strides=1, padding="SAME", activation="relu",
                               input_shape=[IMG_HEIGHT, IMG_WIDTH, 1]),  # Convolution with zero padding
        tf.keras.layers.MaxPooling2D(pool_size=2),  # Taking max value from 2x2 sub-matrices
        tf.keras.layers.Flatten(),  # Re-stacks layers n to single m * n array
        tf.keras.layers.Dense(128, activation='relu'),  # Fully connected layer
        tf.keras.layers.Dropout(0.5),  # 50% dropout to avoid over fitting
        tf.keras.layers.Dense(num_classes),  # Fully connected layer with number of nodes = number of classes
        tf.keras.layers.Softmax()  # Normalise output to class probabilities
    ])

    # Loss function measures accuracy during training
    # Accuracy = fraction of images correctly classified
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                  metrics=['accuracy'])

    return model


def partition_ds(ds: tf.data.Dataset, train_split: float = 0.8, val_split: float = 0.1, test_split: float = 0.1):

    assert (train_split + test_split + val_split) == 1

    ds_size = len(ds)

    train_size = int(train_split * ds_size)
    val_size = int(val_split * ds_size)

    train_ds = ds.take(train_size)
    val_ds = ds.skip(train_size).take(val_size)
    test_ds = ds.skip(train_size).skip(val_size)

    return train_ds, val_ds, test_ds


def get_image_label_from_path(file_path, class_names: np.array, channels: int = 1) -> (tf.Tensor, tf.int64):
    # Convert the path to a list of path components
    parts = tf.strings.split(file_path, os.path.sep)
    # The second to last is the class-directory
    one_hot = parts[-2] == class_names
    # Integer encode the label
    label = tf.argmax(one_hot)
    # Load the raw data from the file as a string
    img = tf.io.read_file(file_path)
    img = tf.io.decode_image(img, channels=channels, expand_animations=False)
    img = tf.image.resize(img, [IMG_HEIGHT, IMG_WIDTH])
    return img, label


def configure_for_performance(ds: tf.data.Dataset) -> tf.data.Dataset:
    ds = ds.cache()
    ds = ds.shuffle(buffer_size=1000)
    ds = ds.batch(BATCH_SIZE)
    ds = ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    return ds


def train(dataset_name: str, dataset_path=None, epochs: int = 10) -> None:

    if dataset_name == EXAMPLE_TF_DATASET or dataset_path is None:

        print('Training fashion mnist example')
        train_ds, val_ds, test_ds, class_names = get_example()
    else:
        print(f"Getting data from {dataset_path}")
        train_ds, val_ds, test_ds, class_names = preprocess(dataset_path)

    train_ds = configure_for_performance(train_ds)
    val_ds = configure_for_performance(val_ds)
    test_ds = configure_for_performance(test_ds)

    model = create_model(len(class_names))
    model.fit(train_ds, validation_data=val_ds, epochs=epochs)
    test_loss, test_acc = model.evaluate(test_ds, verbose=2)
    print(f"\nTest accuracy: {round(test_acc * 100, 2)}%")

    # TODO: Save class names
    # Saving
    pathlib.Path.mkdir(pathlib.Path(MODEL_DIR), exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_name = '_'.join((dataset_name, timestamp))
    model.save(pathlib.Path(MODEL_DIR, model_name))


def preprocess(dataset_path: pathlib.Path):

    list_ds = tf.data.Dataset.list_files(str(dataset_path.joinpath('*', '*')), shuffle=False)
    list_ds = list_ds.shuffle(len(list_ds), seed=0, reshuffle_each_iteration=True)
    train_ds, val_ds, test_ds = partition_ds(list_ds)

    class_names = np.array(sorted([item.name for item in dataset_path.glob('*') if os.path.isdir(item)]))

    train_ds = train_ds.map(lambda x: get_image_label_from_path(x, class_names), num_parallel_calls=tf.data.AUTOTUNE)
    val_ds = val_ds.map(lambda x: get_image_label_from_path(x, class_names), num_parallel_calls=tf.data.AUTOTUNE)
    test_ds = test_ds.map(lambda x: get_image_label_from_path(x, class_names), num_parallel_calls=tf.data.AUTOTUNE)

    return train_ds, val_ds, test_ds, class_names


def get_example():

    (train_ds, val_ds, test_ds), metadata = tfds.load(
        EXAMPLE_TF_DATASET,
        split=['train[:80%]', 'train[80%:90%]', 'train[90%:]'],
        with_info=True,
        as_supervised=True,
    )

    class_names = np.array(sorted(metadata.features["label"].names))
    return train_ds, val_ds, test_ds, class_names


def main():

    parser = argparse.ArgumentParser(
        description="Training a CNN based on specified dataset"
    )

    parser.add_argument("--dataset",
                        default=EXAMPLE_TF_DATASET,
                        help=f"Specify dataset within dataset directory ({DATASET_DIR})",
                        )

    parser.add_argument("--epochs",
                        default=50,
                        type=int,
                        help=f"Number of training cycles",
                        )

    # TODO: Allow image size to be set, potentially remove from settings or change to DEFAULT_IMG_SIZE
    # parser.add_argument("--imagesize")

    args = parser.parse_args()

    if args.dataset == EXAMPLE_TF_DATASET:
        dataset_path = None
    else:
        dataset_path = pathlib.Path(DATASET_DIR, args.dataset)
        if not pathlib.Path.is_dir(dataset_path):
            raise NotADirectoryError(f"Dataset {args.dataset} not found in {DATASET_DIR}")

    train(args.dataset, dataset_path, epochs=args.epochs)


if __name__ == "__main__":

    main()
