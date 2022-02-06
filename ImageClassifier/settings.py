import os

# Paths
dirpath = os.path.dirname(__file__)
DATASET_DIR = os.path.join(dirpath, "datasets")
MODEL_DIR = os.path.join(dirpath, "saved_models")

# Model
EXAMPLE_DATASET = "fashion_mnist"
BATCH_SIZE = 32
IMG_HEIGHT = 28
IMG_WIDTH = 28
