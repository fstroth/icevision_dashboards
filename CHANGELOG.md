# CHANGELO

# Version - 0.0.6

    - Instance segmentation integration supplying all the same functionality as for object detection
      - DashboardDataset integration
      - Dashboards
      - Metric
    - Additional stats for results of object detction and instance segmentation (x-,y-offsets for bboxes and masks and many others) 
    - Notebooks to generate test data for tests that require specific data
    - Additional examples on how to use the library
    - Added Dashboard to find optimal aspect ratios for anchor box creation
    - Generic integration for losses, this allows for all object detection models to work without specifing how the loss is named for the result dashboard
    - Fixed CI pipeline
    - Library now works with python 3.7
    - Update to the new icevision (0.11.0) and icedata (0.5.0) versions 