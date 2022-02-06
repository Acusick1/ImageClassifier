import os
import pathlib
import argparse
import settings
import tensorflow as tf
import tensorflow_datasets as tfds
import numpy as np
from datetime import datetime


def create_model(num_classes: int) -> tf.keras.Sequential:

    model = tf.keras.Sequential([
        tf.keras.layers.Rescaling(1./255),
        tf.keras.layers.Flatten(input_shape=[settings.IMG_HEIGHT, settings.IMG_WIDTH]),  # Re-stacks layers n to single m * n array
        tf.keras.layers.Dense(128, activation='relu'),  # Fully connected layer
        tf.keras.layers.Dense(num_classes),  # Fully connected layer with number of nodes = number of classes
        tf.keras.layers.Softmax()  # Normalise output to class probabilities
    ])

    # Loss function measures accuracy during training
    # Metrics used to monitor training and testing steps. Accuracy = fraction of images correctly classified
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
    img = tf.image.resize(img, [settings.IMG_HEIGHT, settings.IMG_WIDTH])
    return img, label


def configure_for_performance(ds: tf.data.Dataset) -> tf.data.Dataset:
    ds = ds.cache()
    ds = ds.shuffle(buffer_size=1000)
    ds = ds.batch(settings.BATCH_SIZE)
    ds = ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    return ds


def train(dataset: str = settings.EXAMPLE_DATASET, epochs: int = 10) -> None:

    if dataset == settings.EXAMPLE_DATASET:

        print('Training fashion mnist example')
        train_ds, val_ds, test_ds, class_names = get_example()
    else:
        dataset_path = pathlib.Path(settings.DATASET_DIR, dataset)
        if not pathlib.Path.is_dir(dataset_path):
            raise NotADirectoryError(f"Dataset {dataset} not found in {settings.DATASET_DIR}")

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
    pathlib.Path.mkdir(pathlib.Path(settings.MODEL_DIR), exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_name = '_'.join((dataset, timestamp))
    model.save(pathlib.Path(settings.MODEL_DIR, model_name))


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
        settings.EXAMPLE_DATASET,
        split=['train[:80%]', 'train[80%:90%]', 'train[90%:]'],
        with_info=True,
        as_supervised=True,
    )

    class_names = np.array(sorted(metadata.features["label"].names))
    return train_ds, val_ds, test_ds, class_names


def main():

    parser = argparse.ArgumentParser(description="Training CNN based on input dataset")
    parser.add_argument("--dataset",
                        default=settings.EXAMPLE_DATASET,
                        help=f"Specify dataset within dataset directory ({settings.DATASET_DIR})",
                        )

    # TODO: Allow image size to be set, potentially remove from settings or change to DEFAULT_IMG_SIZE
    # parser.add_argument("--imagesize")

    args = parser.parse_args()

    train(args.dataset)


if __name__ == "__main__":

    main()
