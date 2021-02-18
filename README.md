# IceVisionDashboard



IceVisionDashboard is an extension to the [IceVision](https://github.com/airctic/icevision) object detection framework. This extension provides different `dashboards` to investigate datasets, create new datasets and analyse the results of a training.

# Contributing

If you want to contribute add the following lines to your `pre-commit` file to ensure the notebook cell output don't get pushed into the repo.

```bash
# ensure the oupt of the notebooks is empty
jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace nbs/*.ipynb
git add .
```
