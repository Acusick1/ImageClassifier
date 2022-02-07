import os
import pathlib

# Paths
parent_path = pathlib.Path(os.path.dirname(__file__))
DATASET_DIR = parent_path.joinpath("datasets")
MODEL_DIR = parent_path.joinpath("saved_models")

# Model
BATCH_SIZE = 32
IMG_HEIGHT = 28
IMG_WIDTH = 28

MODELS = [f.name for f in MODEL_DIR.iterdir() if f.is_dir()]
DATASETS = [f.name for f in DATASET_DIR.iterdir() if f.is_dir()]

# Used to download from tf datasets
EXAMPLE_TF_DATASET = "fashion_mnist"
TF_MODELS = [m for m in MODELS if EXAMPLE_TF_DATASET in m]
# Selecting most recent as default
# TODO: Remove/rename MNIST to generic name once predictor works for other datasets, have function that selects most
#  recent
DEFAULT_MNIST_MODEL = TF_MODELS[-1] if TF_MODELS else f"Train a model {EXAMPLE_TF_DATASET} first!"
