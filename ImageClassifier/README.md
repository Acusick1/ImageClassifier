# ImageClassifier
A simple multi-class CNN image classifier using TensorFlow.
## Instructions
The image classifier is run using the project top level `trainer.py` script. By default, this will train a model using the fashion MNIST dataset. Note that TensorFlow will download this dataset if it has not been downloaded previously, which may take a few minutes depending on bandwidth.

Following training, models are saved and stored within `ImageClassifier/saved_models`.

To train a different dataset, place it within the `ImageClassifier/datasets` directory. Note that the dataset must be in the format `dataset_name/class_names/class_images`. 

Then, run the trainer using the following command:

```commandline
$ python trainer.py --dataset dataset_name
```

A small number of training cycles (epochs) are used by default, to change this use the `epochs` argument. For example:

```commandline
$ python trainer.py --dataset dataset_name --epochs 50
```

At the moment these are the only command options. However, additional settings such as image size can be changed in `ImageClassifier/settings.py`.

Run ``$ python trainer.py -h`` to view command line options.

## Next steps
- Testing suite
- Additional training options (padded convolution layer, KFold cross validation)
- Additional command line options (training method, image size, arguments to be passed to model.fit)
- Save class names alongside model for use in App