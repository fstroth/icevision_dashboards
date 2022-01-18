# IceVisionDashboard



[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/fstroth/icevision_dashboards/HEAD)


IceVisionDashboard is an extension to the [IceVision](https://github.com/airctic/icevision) object detection framework. Main goal of the library is to support data scientists with there work on object detection problems. This is done by providing different dashboards to provide different steps of the workflow. The dashboards cover investigating datasets, creating new datasets, comparing datasets and analyzing the results of a training.

## Test stuff

## Example

The example shows how a set of records (here the training_records) can be visualized with the dashboard lib to get some fast insights into the data. The last 3 lines of code are from the dashboard library all the lines before are usual icevision code.

```python
from icevision_dashboards.data import BboxRecordDataset
from icevision_dashboards.dashboards import ObjectDetectionDatasetOverview
# load some data from the icedata
data_dir = icedata.fridge.load_data()
class_map = icedata.fridge.class_map()
parser = icedata.fridge.parser(data_dir)
train_records, valid_records = test_parser.parse()
# create a dataset that can be consumed by the dashboards
train_dash_ds = BboxRecordDataset(train_records, class_map)
# create a new dashboard instance and display it with the .show() function
overview_dashboard = ObjectDetectionDatasetOverview(train_dash_ds, width=1500, height=900)
overview_dashboard.show()
```

The output will look like this:

An overview of some descriptive statistics for the dataset, the images and the classes.
<div style="text-align:center"><img src="imgs/dataset_overview_0.png" /></div>

Some more indepth information about the classes, how they mix (how often they appear at the same time in an image), distribution of annotations per image and a 2D histogram that can be customized. 
<div style="text-align:center"><img src="imgs/dataset_overview_1.png" /></div>

A gallery with sorting functionality of have a direct look at the images.
<div style="text-align:center"><img src="imgs/dataset_overview_2.png" /></div>

Tabular representation of all annotations.
<div style="text-align:center"><img src="imgs/dataset_overview_3.png" /></div>

# Install

IceVisionDashboard is available as a `pip` package via PyPi. To install, simply type:

```shell
pip install icevision-dashboards
```

If you are using JupyterLab to view and use your notebooks, a few extra steps are needed. In a terminal, you should type the following:

```shell
jupyter labextension install @pyviz/jupyterlab_pyviz
```

And then in a new cell inside the notebook in which you want to load IceVision dashboards, you should type and execute the following code:

```python
import panel
panel.extension()
```

# Contributing

If you want to contribute add the following lines to your `pre-commit` file to ensure the notebook cell output don't get pushed into the repo.

```bash
# ensure the oupt of the notebooks is empty
jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace nbs/*.ipynb
jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace examples/*.ipynb
jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace test_data_generation/*.ipynb
nbdev_build_lib
git add .
```
