# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/dashboards.ipynb (unless otherwise specified).

__all__ = ['ObjectDetectionDatasetOverview', 'ObjectDetectionDatasetComparison',
           'ObjectDetectionDatasetGeneratorScatter', 'ObjectDetectionDatasetGeneratorRange',
           'ObjectDetectionResultOverview', 'InstanceSegmentationDatasetOverview',
           'InstanceSegmentationDatasetComparison', 'InstanceSegmentationDatasetGeneratorScatter',
           'InstanceSegmentationDatasetGeneratorRange', 'InstanceSegmentationResultOverview']

# Cell
from typing import Union, Optional, List
from abc import abstractmethod, ABC
from math import ceil, floor
import itertools

import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

from bokeh.plotting import show, output_notebook, gridplot, figure
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.models import ColumnDataSource, HoverTool, Title
from bokeh import events

import panel as pn
import panel.widgets as pnw
import numpy as np
import pandas as pd

from .core.dashboards import *
from .plotting import *
from .core.data import *
from .data import *
from .plotting.utils import toggle_legend_js

# Cell
class ObjectDetectionDatasetOverview(DatasetOverview):
    """Dataset overview for object detection datasets"""
    DESCRIPTOR_DATA = "data"
    DESCRIPTOR_STATS_DATASET = "stats_dataset"
    DESCRIPTOR_STATS_IMAGES = "stats_image"
    DESCRIPTOR_STATS_ANNOTATIONS = "stats_class"

    # change these
    IMAGE_IDENTIFIER_COL = "filepath"
    ANNOTATON_LABEL_COL = "label"
    OBJECTS_PER_IMAGE_COL = "num_annotations"
    AREA_COL = "area"

    def __init__(self, dataset: GenericDataset, height: int = 500, width: int = 500):
        super().__init__(dataset, height, width)
        _, cluster_centers, _ = self._run_kmeans_clustering(3)
        self.aspect_ratios = cluster_centers

    def _run_kmeans_clustering(self, number_of_clusters, max_iter=1000):
        normalized_aspect_ratios = self.dataset.data["bbox_ratio"].values
        kmeans = KMeans(init='random', n_clusters=number_of_clusters, random_state=0, max_iter=max_iter)
        predictions = kmeans.fit_predict(X=np.expand_dims(normalized_aspect_ratios, -1))
        cluster_centers = kmeans.cluster_centers_
        return predictions, cluster_centers, normalized_aspect_ratios

    def _generate_anchor_tab(self):
        num_clusters = pnw.NumberInput(name="Number of aspect ratios", value=3, width=self.width, height=50)
        num_bins = pnw.NumberInput(name="Bins", value=30, width=self.width, height=50)

        @pn.depends(num_clusters.param.value, num_bins.param.value)
        def _plot(num_clusters, bins):
            nonlocal self
            predictions, cluster_centers, normalized_aspect_ratios = self._run_kmeans_clustering(num_clusters)
            self.aspect_ratios = cluster_centers
            fig, ax = plt.subplots(1,1, figsize=(16,9))
            for pred_label, center in enumerate(cluster_centers):
                ax.hist(normalized_aspect_ratios[predictions==pred_label], bins=bins, range=(normalized_aspect_ratios.min(), normalized_aspect_ratios.max()), label=f"Center: {round(float(center), 2)}")
                ax.set_xlabel("Aspect ratios", fontsize=24)
                ax. tick_params(axis='both', labelsize=20)
            ax.legend(fontsize=25)
            plt.close()
            return pn.Column(
                pnw.TextInput(name="Aspect Ratios", value=f"{[round(float(i), 2) for i in cluster_centers]}", align="center", disabled=True, width=self.width, height=50),
                pn.pane.Matplotlib(fig, width=int((self.height-150)*(16/9)), height=self.height-150, align="center")
            )
        return pn.Column(num_clusters, num_bins, _plot)

    def _generate_datset_stats_tab(self):
        dataset_overview_table = table_from_dataframe(getattr(self.dataset, self.DESCRIPTOR_STATS_DATASET), width=self.width, height=self.height//7)
        images_overview_table = table_from_dataframe(getattr(self.dataset, self.DESCRIPTOR_STATS_IMAGES), width=self.width, height=self.height//7)
        classes_overview_table = table_from_dataframe(getattr(self.dataset, self.DESCRIPTOR_STATS_ANNOTATIONS), width=self.width, height=self.height//4)

        class_occurances = self.dataset.data.groupby("label").count()["id"]
        class_occurance_barplot = barplot(counts=class_occurances.values, values=np.array(class_occurances.index), bar_type="vertical", height=(self.height//5)*2)

        return pn.Column("<b>Dataset stats</b>", dataset_overview_table, "<b>Image stats</b>", images_overview_table, "<b>Class stats</b>", classes_overview_table, pn.Row(class_occurance_barplot, align="center"))

    def _generate_annotations_tab(self):
        plot_width, plot_height = floor(self.width*0.45), floor(self.height*0.45)
        # mixing of classes
        mixing_matrix_classes_in_images = utils.calculate_mixing_matrix(getattr(self.dataset, self.DESCRIPTOR_DATA), self.IMAGE_IDENTIFIER_COL, self.ANNOTATON_LABEL_COL)
        self.class_mixing_matrix_plot = pn.Column("<b>Class mixing</b>", heatmap(mixing_matrix_classes_in_images, "row_name", "col_name", "values", width=plot_width, height=plot_height), height=self.height)
        # number of object per image, stacked hist
        self.classes_for_objects_per_image_stacked_hist = pn.Column(
            "<b>Objects per Image</b>",
            stacked_hist(getattr(self.dataset, self.DESCRIPTOR_DATA), self.OBJECTS_PER_IMAGE_COL, self.ANNOTATON_LABEL_COL, "Objects per Image", width=plot_width, height=plot_height)
        )
        # categorical overview
        self.categorical_2d_histogram = categorical_2d_histogram_with_gui(
            getattr(self.dataset, self.DESCRIPTOR_DATA),
            category_cols=["label", "num_annotations", "width", "height"],
            hist_cols=["num_annotations", "area", "area_normalized", "area_square_root", "area_square_root_normalized", "bbox_ratio", "bbox_xmin", "bbox_xmax", "bbox_ymin", "bbox_ymax", "width", "height"],
            height=self.height//2, width=self.width//2
        )
        # ratio distribution
        grid =  pn.GridSpec(ncols=2,nrows=2, width=self.width, height=self.height, align="center")
        grid[0,0] = self.class_mixing_matrix_plot
        grid[1,0] = self.classes_for_objects_per_image_stacked_hist
        grid[:,1] = pn.Column(self.categorical_2d_histogram, align="center")
        return grid

    def _generate_gallery_tab(self):
        return pn.Column(Gallery(self.dataset, "data", "filepath", ["num_annotations", "width", "height", "label", "area", "bbox_ratio", "bbox_width", "bbox_height"], height=self.height).show(), align="center", sizing_mode="stretch_both")

    def build_gui(self):
        dataset_tab = super()._generate_dataset_tab()
        dataset_stats_tab = self._generate_datset_stats_tab()
        annotations_tab = self._generate_annotations_tab()
        anchor_tab = self._generate_anchor_tab()
        gallery_tab = self._generate_gallery_tab()
        self.gui = pn.Tabs(("Dataset stats", dataset_stats_tab), ("Annotations", annotations_tab), ("Aspect Ratios", anchor_tab), ("Gallery", gallery_tab), ("Dataset", dataset_tab), align="start")

# Cell
class ObjectDetectionDatasetComparison(DatasetComparison):
    """Dataset comparison for object detection datasets."""
    DESCRIPTOR_DATA = "data"
    DESCRIPTOR_STATS_DATASET = "stats_dataset"
    DESCRIPTOR_STATS_IMAGES = "stats_image"
    DESCRIPTOR_STATS_ANNOTATIONS = "stats_class"

    # change these
    IMAGE_IDENTIFIER_COL = "filepath"
    ANNOTATON_LABEL_COL = "label"
    OBJECTS_PER_IMAGE_COL = "num_annotations"
    AREA_COL = "area"

    def _generate_dataset_tab(self):
        overview_table = table_from_dataframe(self._get_descriptor_for_all_datasets(self.DESCRIPTOR_DATA), width=floor(self.width/2), height=self.height)
        return pn.Row(*overview_table)

    def _generate_datset_stats_tab(self):
        dataset_overview_table = table_from_dataframe(self._get_descriptor_for_all_datasets(self.DESCRIPTOR_STATS_DATASET), width=floor(self.width/2), height=self.height//7)
        images_overview_table = table_from_dataframe(self._get_descriptor_for_all_datasets(self.DESCRIPTOR_STATS_IMAGES), width=floor(self.width/2), height=self.height//7)
        classes_overview_table = table_from_dataframe(self._get_descriptor_for_all_datasets(self.DESCRIPTOR_STATS_ANNOTATIONS), width=floor(self.width/2), height=self.height//4)

        class_occurances_values = [dataset.data.groupby("label").count()["id"].values for dataset in self.datasets]
        class_occurances_index = [np.array(dataset.data.groupby("label").count()["id"].index) for dataset in self.datasets]
        class_occurance_barplot = barplot(counts=class_occurances_values, values=class_occurances_index, bar_type="vertical", height=(self.height//5)*2, width=floor(self.width/2))

        dublication_data = {dataset.name if dataset.name is not None else "Dataset_"+str(index): [getattr(dataset, self.DESCRIPTOR_DATA).duplicated().sum()] for index, dataset in enumerate(self.datasets)}
        dublication_data["All"] = pd.concat(self._get_descriptor_for_all_datasets(self.DESCRIPTOR_DATA)).duplicated().sum()
        dublication_df = pd.DataFrame(dublication_data)
        dublication_overview = table_from_dataframe(dublication_df)

        return pn.Column(
            "<b>Dublications</p>", pn.Row(dublication_overview),
            "<b>Dataset stats</b>", pn.Row(*dataset_overview_table),
            "<b>Image stats</b>", pn.Row(*images_overview_table),
            "<b>Class stats</b>", pn.Row(*classes_overview_table),
            pn.Row(*class_occurance_barplot, align="center")
        )

    def _generate_annotations_tab(self):
        plot_size = min(floor(self.width/len(self.datasets)), floor(self.height/2))
        link_plots_checkbox = pnw.Checkbox(name="Link plot axis", value=False)

        @pn.depends(link_plots_checkbox.param.value)
        def _mixing_plots(link_plots):
            # mixing of classes
            mixing_matrix_classes_in_images = [utils.calculate_mixing_matrix(dataset, self.IMAGE_IDENTIFIER_COL, self.ANNOTATON_LABEL_COL) for dataset in self._get_descriptor_for_all_datasets(self.DESCRIPTOR_DATA)]
            class_mixing_matrix_plot = pn.Row("<b>Class mixing</b>", *heatmap(mixing_matrix_classes_in_images, "row_name", "col_name", "values", link_plots=link_plots, width=plot_size, height=plot_size))
            # number of object per image, stacked hist
            classes_for_objects_per_image_stacked_hist = pn.Row(
                "<b>Objects per Image</b>",
                *stacked_hist(self._get_descriptor_for_all_datasets(self.DESCRIPTOR_DATA), self.OBJECTS_PER_IMAGE_COL, self.ANNOTATON_LABEL_COL, "Objects per Image", link_plots=link_plots, width=plot_size, height=plot_size)
            )
            return pn.Column(link_plots_checkbox, class_mixing_matrix_plot, classes_for_objects_per_image_stacked_hist)

        # categorical overview
        self.categorical_2d_histogram = categorical_2d_histogram_with_gui(
            self._get_descriptor_for_all_datasets(self.DESCRIPTOR_DATA),
            category_cols=["label", "num_annotations", "width", "height"],
            hist_cols=["num_annotations", "area", "area_normalized", "area_square_root", "area_square_root_normalized", "bbox_ratio", "bbox_xmin", "bbox_xmax", "bbox_ymin", "bbox_ymax", "bbox_width", "bbox_height", "width", "height"],
            height=floor(plot_size*1.5), width=floor(plot_size*1.5)
        )
        return pn.Row(_mixing_plots, self.categorical_2d_histogram, align="center")

    def _generate_gallery_tab(self):
        return pn.Row(*[Gallery(dataset, "data", "filepath", ["num_annotations", "width", "height", "label", "area", "bbox_ratio", "bbox_width", "bbox_height"], width=floor(self.width/len(self.datasets))).show() for dataset in self.datasets], align="start", sizing_mode="stretch_both")

    def build_gui(self):
        dataset_tab = self._generate_dataset_tab()
        dataset_stats_tab = self._generate_datset_stats_tab()
        annotations_tab = self._generate_annotations_tab()
        gallery_tab = self._generate_gallery_tab()
        self.gui = pn.Tabs(("Dataset stats overview", dataset_stats_tab), ("Annotations overivew", annotations_tab), ("Gallery", gallery_tab), ("Dataset overview", dataset_tab), align="start")

# Cell
class ObjectDetectionDatasetGeneratorScatter(DatasetGeneratorScatter):
    """Dataset generator for object detection"""
    DESCRIPTOR_STATS = "stats_dataset"
    DATASET_OVERVIEW = ObjectDetectionDatasetOverview
    DATASET_FILTER_COLUMNS = ["width", "height", "label", "area_normalized", "bbox_ratio", "bbox_width", "bbox_height", "num_annotations"]

# Cell
class ObjectDetectionDatasetGeneratorRange(DatasetGenerator):
    """Dataset generator for object detection"""
    DESCRIPTOR_STATS = "stats_dataset"
    DATASET_OVERVIEW = ObjectDetectionDatasetOverview
    DATASET_FILTER_COLUMNS = ["width", "height", "label", "area_normalized", "bbox_ratio", "bbox_width", "bbox_height", "num_annotations"]

# Cell
class ObjectDetectionResultOverview(Dashboard):
    """Overview dashboard """
    def __init__(self, dataset, height=700, width=1000):
        self.dataset= dataset
        self.accordion_active = [0]
        self.loss_keys = [key for key in self.dataset.base_data.columns if "loss" in key]
        super().__init__(width=width, height=height)

    def build_gui(self):
        self.loss_tab = self.build_loss_tab()
        self.ap_tab = self.build_precision_recall_tab()
        self.gui = pn.Tabs(("Loss", self.loss_tab), ("Precision-Recall", self.ap_tab))

    def show(self):
        return self.gui

    def show_loss_tab(self):
        return self.loss_tab

    def show_ap_tab(self):
        return self.ap_tab

    @staticmethod
    def generate_grid_coodinates(num_centers, center_spacer_ratio=3.5):
        num_spacers = num_centers+1
        spacer_size = 1/(num_spacers*center_spacer_ratio)
        center_size = (1-num_spacers*spacer_size)/num_centers
        coordinates = []
        coordinate1 = 0
        coordinate = spacer_size
        for i in range(num_spacers + num_centers - 1):
            if i%2:
                coordinate += spacer_size
            else:
                coordinates.append((coordinate, coordinate+center_size))
                coordinate += center_size
        return coordinates

    def build_loss_tab(self):
        # loss hists
        fig_loss_hists, ax_loss_hists = plt.subplots(1, len(self.loss_keys), figsize=(16*5,9))
        unique_losses = self.dataset.base_data[["filepath"] + self.loss_keys].drop_duplicates()
        for single_ax, key in zip(ax_loss_hists, self.loss_keys):
            single_ax.hist(unique_losses[key].values, bins=20)
            single_ax.set_title(" ".join(key.split("_")).title(), fontsize=40)
            for tick in single_ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(34)
                tick.label.set_rotation(45)
            for tick in single_ax.yaxis.get_major_ticks():
                tick.label.set_fontsize(34)
        plt.tight_layout()
        plt.close()
        loss_hists_col = pn.pane.Matplotlib(fig_loss_hists, width=self.width)
        axis_cols = ['score', 'area_normalized', 'area', 'bbox_ratio', 'bbox_width', 'bbox_height', 'num_annotations'] + self.loss_keys + ['width', 'height']
        scatter_overview = scatter_plot_with_gui(
            self.dataset.base_data[self.dataset.base_data["is_prediction"] == True],
            x_cols=axis_cols[1:] + [axis_cols[0]],
            y_cols=axis_cols,
            color_cols=["label", "num_annotations", "filename"]
        )

        cat_2d_hist = categorical_2d_histogram_with_gui(
            self.dataset.base_data[self.dataset.base_data["is_prediction"] == True],
            category_cols=["label", "num_annotations", "filename"],
            hist_cols=self.loss_keys + ['score', 'area_normalized', 'area', 'bbox_ratio', 'bbox_width', 'bbox_height', 'num_annotations', 'width', 'height', 'label']
        )

        sub_tabs = pn.Tabs(
            ("Histograms", pn.Row(pn.Spacer(sizing_mode="stretch_width"), scatter_overview, pn.Spacer(sizing_mode="stretch_width"), cat_2d_hist, pn.Spacer(sizing_mode="stretch_width"), align="center")),
            ("Gallery", Gallery(self.dataset, "base_data", "filepath", sort_cols=self.loss_keys, height=self.height).show())
        )

        return pn.Column(loss_hists_col, sub_tabs)

    def build_ap_overview(self, metric_data):
        map_data = {key: [metric_data[key]["map"], int(len(metric_data[key].keys())-1)] for key in metric_data.keys()}
        map_table = table_from_dataframe(pd.DataFrame(map_data, index=["mAP", "Classes"]).round(4))

        ap_data = {}
        for metric_key, metric_value in metric_data.items():
            if metric_key != "map":
                ap_data[metric_key] = {"class": [], "ap": []}
                for class_name, class_data in metric_value.items():
                    if class_name != "map":
                        ap_data[metric_key]["class"].append(class_name)
                        ap_data[metric_key]["ap"].append(class_data["ap"])
        ap_plots = []
        for ap_key, ap_value in ap_data.items():
            if len(ap_value["ap"]) > 0:
                ap = np.array(ap_value["ap"])[np.array(ap_value["ap"]).argsort()]
                class_names = np.array(ap_value["class"])[np.array(ap_value["ap"]).argsort()]
                ap_plot = barplot(ap, class_names, bar_type="horizontal")
                ap_plot.add_tools(HoverTool(tooltips = [("AP", "@y @right")]))
                ap_plot.title = Title(text="mAP - " + str(metric_data[ap_key]["map"].round(4)), align="center")
                ap_plots.append(pn.Column("<b>"+ap_key.replace("_", " ").title().replace("Ap", "AP")+"</b>", ap_plot))

        return pn.Column(pn.Row(map_table, align="center"), pn.Row(*ap_plots, align="center"))

    @staticmethod
    def precision_recall_plot_matplotlib(fig, data, iou, bottom, top, left, right):
        gs = fig.add_gridspec(nrows=4, ncols=1, left=left, right=right, bottom=bottom, top=top, hspace=0)
        ax1 = fig.add_subplot(gs[:3, :])
        ax1.set_title("IOU: " + str(iou))
        ax1.plot(data["recall"], data["precision"], label="Actual", color="black", lw=2)
        ax1.plot(data["ap11_recalls"], data["ap11_precisions"], label="AP11", color="green", lw=2)
        ax1.plot(data["monotonic_recalls"], data["monotonic_precisions"], label="Montonic", color="firebrick", lw=2)
        ax1.set_xticks([])
        ax1.set_ylabel("Precision")
        ax1.legend()
        ax2 = fig.add_subplot(gs[-1, :])
        ax2.plot(data["recall"], data["scores"], ".")
        ax2.set_xlabel("Recall")
        ax2.set_ylabel("Score")

    def plot_precision_recall_curves_for_class_matplotlib(self, data, class_key):
        fig = plt.figure(constrained_layout=False, figsize=(16,9))
        row_coords = self.generate_grid_coodinates(2)[::-1]
        col_coords = self.generate_grid_coodinates(5)
        coord_combinations = list(itertools.product(row_coords, col_coords))
        ious = sorted([iou for iou in data.keys() if iou != "ap"])
        for index, iou in enumerate(ious):
            if iou != "ap":
                row_coord = coord_combinations[index][0]
                col_coord = coord_combinations[index][1]
                self.precision_recall_plot_matplotlib(fig, data[iou], iou, row_coord[0], row_coord[1], col_coord[0], col_coord[1])
        plt.close()
        return pn.pane.Matplotlib(fig, width=self.width)

    @staticmethod
    def histogramm_plot(fig, data, hist_key, bottom, top, left, right, bins=25):
        gs = fig.add_gridspec(nrows=1, ncols=1, left=left, right=right, bottom=bottom, top=top, hspace=0)
        ax = fig.add_subplot(gs[:, :])
        # ax.set_title(hist_key)
        if not "scatter" in hist_key:
            if "normalized" in hist_key:
                ax.hist(data[hist_key][0], bins=bins, range=(0,1))
            else:
                ax.hist(data[hist_key][0], bins=bins)
            ax.set_xlabel(" ".join(hist_key.split("_")).title())
            ax.set_ylabel("Counts")
        elif hist_key == "used_scatter":
            ax.plot(data["used_gt_box_areas_normalized"][0], data["used_pred_box_areas_normalized"][0], ".")
            ax.set_xlabel('Used Gt Box Areas Normalized')
            ax.set_ylabel('Used Pred Box \nAreas Normalized')
        elif hist_key == "unused_scatter":
            ax.plot(data["unused_gt_box_areas_normalized"][0], data["unused_pred_box_areas_normalized"][0], ".")
            ax.set_xlabel('Unused Gt Box Areas Normalized')
            ax.set_ylabel('Unused Pred Box \nAreas Normalized')
        elif hist_key == "xoffset_vs_yoffset_scatter":
            ax.plot(data["x_center_offsets"][0], data["y_center_offsets"][0], ".")
            ax.set_ylabel("Y-Offset")
            ax.set_xlabel("X-Offset")
        elif hist_key == "center_distance_vs_unused_gt_box_area_scatter":
            ax.plot(data["center_distances"][0], data["unused_gt_box_areas_normalized"][0], ".")
            ax.set_ylabel('Unused Gt Box \nAreas Normalized')
            ax.set_xlabel("Center Distance")
        elif hist_key == "center_distance_vs_unused_pred_box_area_scatter":
            ax.plot(data["center_distances"][0], data["unused_pred_box_areas_normalized"][0], ".")
            ax.set_ylabel('Unused Pred Box \nAreas Normalized')
            ax.set_xlabel("Center Distance")

    def plot_additional_stats_matplotlib(self, class_data, class_name):
        # histograms
        ious = sorted([iou for iou in class_data.keys() if iou != "ap"])
        iou_selector = pnw.Select(name="IOU", options=ious, value=0.5)

        @pn.depends(iou_selector.param.value)
        def _plot_additional_stats_matplotlib(iou):
            nonlocal class_data
            nonlocal self
            data = class_data[iou]
            fig = plt.figure(constrained_layout=False, figsize=(16,9))
            row_coords = self.generate_grid_coodinates(3)[::-1]
            col_coords = self.generate_grid_coodinates(4)[::-1]
            coord_combinations = list(itertools.product(col_coords, row_coords))

            for index, hist_key in enumerate(
                [
                    'center_distances', 'y_center_offsets', 'x_center_offsets',
                    'used_scatter', 'unused_gt_box_areas_normalized', 'used_gt_box_areas_normalized',
                    'unused_scatter', 'center_distances', 'y_center_offsets',
                    'xoffset_vs_yoffset_scatter', 'center_distance_vs_unused_gt_box_area_scatter', "center_distance_vs_unused_pred_box_area_scatter",
                ]
            ):
                row_coord = coord_combinations[index][0]
                col_coord = coord_combinations[index][1]
                self.histogramm_plot(fig, data, hist_key, row_coord[0], row_coord[1], col_coord[0], col_coord[1])
            plt.close()
            return pn.pane.Matplotlib(fig, width=self.width)
        return pn.Column(iou_selector, _plot_additional_stats_matplotlib)

    def build_precison_recall_overview(self, data):
        if len(data) == 1:
            return pn.Column("<h1> No information available</h1>")
        class_select = pnw.Select(options=[key for key in data.keys() if key != "map"])
        @pn.depends(class_select.param.value)
        def _plot(class_name):
            heading = pn.Row("<h1>AP - "+str(data[class_name]["ap"].round(4))+"</h1>", align="center")
            table_data = {"AP": [round(data[class_name][iou_key]["ap"],4) for iou_key in data[class_name].keys() if iou_key != "ap"]}
            table_df = pd.DataFrame(table_data).T
            table_df.columns = [iou_key for iou_key in data[class_name].keys() if iou_key != "ap"]
            table_df.index.names = ["iou"]
            overview_table = table_from_dataframe(table_df)
            precision_recall_curves = self.plot_precision_recall_curves_for_class_matplotlib(data[class_name], class_name)
            additional_stats_plot = self.plot_additional_stats_matplotlib(data[class_name], class_name)
            ap_and_additional_stats_accordion = pn.Accordion(("AP", pn.Column(class_select, heading, pn.Row(overview_table, align="center"), precision_recall_curves)), ("Additioanl stats", additional_stats_plot), active=self.accordion_active)
            return pn.Column(ap_and_additional_stats_accordion)
        return pn.Column(_plot, width=self.width)

    def build_precision_recall_tab(self):
        overview_tab = self.build_ap_overview(self.dataset.metric_data_ap)
        ap_tab = self.build_precison_recall_overview(self.dataset.metric_data_ap["AP"])
        ap_small_tab = self.build_precison_recall_overview(self.dataset.metric_data_ap["AP_small"])
        ap_medium_tab = self.build_precison_recall_overview(self.dataset.metric_data_ap["AP_medium"])
        ap_large_tab = self.build_precison_recall_overview(self.dataset.metric_data_ap["AP_large"])

        return pn.Tabs(("Overview", overview_tab), ("AP", ap_tab), ("AP_small", ap_small_tab), ("AP_medium", ap_medium_tab), ("AP_large", ap_large_tab))

# Cell
class InstanceSegmentationDatasetOverview(ObjectDetectionDatasetOverview):
    pass

# Cell
class InstanceSegmentationDatasetComparison(ObjectDetectionDatasetComparison):
    pass

# Cell
class InstanceSegmentationDatasetGeneratorScatter(DatasetGeneratorScatter):
    """Dataset generator for object detection"""
    DESCRIPTOR_STATS = "stats_dataset"
    DATASET_OVERVIEW = InstanceSegmentationDatasetOverview
    DATASET_FILTER_COLUMNS = ["width", "height", "label", "mask_area", "bbox_area", "bbox_ratio", "bbox_width", "bbox_height", "num_annotations"]

# Cell
class InstanceSegmentationDatasetGeneratorRange(DatasetGenerator):
    """Dataset generator for object detection"""
    DESCRIPTOR_STATS = "stats_dataset"
    DATASET_OVERVIEW = InstanceSegmentationDatasetOverview
    DATASET_FILTER_COLUMNS = ["width", "height", "label", "mask_area", "bbox_area", "bbox_ratio", "bbox_width", "bbox_height", "num_annotations"]

# Cell
class InstanceSegmentationResultOverview(ObjectDetectionResultOverview):
    """Overview dashboard """
    def build_loss_tab(self):
        # loss hists
        fig_loss_hists, ax_loss_hists = plt.subplots(1, len(self.loss_keys), figsize=(16*5,9))
        unique_losses = self.dataset.base_data[["filepath"] + self.loss_keys].drop_duplicates()
        for single_ax, key in zip(ax_loss_hists, self.loss_keys):
            single_ax.hist(unique_losses[key].values, bins=20)
            single_ax.set_title(" ".join(key.split("_")).title(), fontsize=40)
            for tick in single_ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(34)
                tick.label.set_rotation(45)
            for tick in single_ax.yaxis.get_major_ticks():
                tick.label.set_fontsize(34)
        plt.tight_layout()
        plt.close()
        loss_hists_col = pn.pane.Matplotlib(fig_loss_hists, width=self.width)
        axis_cols = ['score', 'mask_area', 'mask_area_normalized', 'mask_area_normalized_by_bbox_area', 'bbox_area_normalized', 'bbox_area', 'bbox_ratio', 'bbox_width', 'bbox_height', 'num_annotations'] + self.loss_keys + ['width', 'height']
        scatter_overview = scatter_plot_with_gui(
            self.dataset.base_data[self.dataset.base_data["is_prediction"] == True],
            x_cols=axis_cols[1:] + [axis_cols[0]],
            y_cols=axis_cols,
            color_cols=["label", "num_annotations", "filename"]
        )

        cat_2d_hist = categorical_2d_histogram_with_gui(
            self.dataset.base_data[self.dataset.base_data["is_prediction"] == True],
            category_cols=["label", "num_annotations", "filename"],
            hist_cols=self.loss_keys + ['score', 'mask_area', 'mask_area_normalized', 'mask_area_normalized_by_bbox_area', 'bbox_area_normalized', 'bbox_area', 'bbox_ratio', 'bbox_width', 'bbox_height', 'num_annotations', 'width', 'height', 'label']
        )

        sub_tabs = pn.Tabs(
            ("Histograms", pn.Row(pn.Spacer(sizing_mode="stretch_width"), scatter_overview, pn.Spacer(sizing_mode="stretch_width"), cat_2d_hist, pn.Spacer(sizing_mode="stretch_width"), align="center")),
            ("Gallery", Gallery(self.dataset, "base_data", "filepath", sort_cols=self.loss_keys, height=self.height).show())
        )

        return pn.Column(loss_hists_col, sub_tabs)

    @staticmethod
    def histogramm_plot(fig, data, hist_key, bottom, top, left, right, bins=25):
        gs = fig.add_gridspec(nrows=1, ncols=1, left=left, right=right, bottom=bottom, top=top, hspace=0)
        ax = fig.add_subplot(gs[:, :])
        # ax.set_title(hist_key)
        if not "scatter" in hist_key:
            if "normalized" in hist_key:
                ax.hist(data[hist_key][0], bins=bins, range=(0,1))
            else:
                ax.hist(data[hist_key][0], bins=bins)
            ax.set_xlabel(" ".join(hist_key.split("_")).title())
            ax.set_ylabel("Counts")
        elif hist_key == "used_scatter":
            ax.plot(data["used_gt_mask_areas_normalized"][0], data["used_pred_mask_areas_normalized"][0], ".")
            ax.set_xlabel('Used Gt Mask Areas Normalized')
            ax.set_ylabel('Used Pred Mask \nAreas Normalized')
        elif hist_key == "unused_scatter":
            ax.plot(data["unused_gt_mask_areas_normalized"][0], data["unused_pred_mask_areas_normalized"][0], ".")
            ax.set_xlabel('Unused Gt Mask Areas Normalized')
            ax.set_ylabel('Unused Pred Mask \nAreas Normalized')
        elif hist_key == "xoffset_vs_yoffset_scatter":
            ax.plot(data["x_center_offsets"][0], data["y_center_offsets"][0], ".")
            ax.set_ylabel("Y-Offset")
            ax.set_xlabel("X-Offset")
        elif hist_key == "center_distance_vs_unused_gt_mask_area_scatter":
            ax.plot(data["center_distances"][0], data["unused_gt_mask_areas_normalized"][0], ".")
            ax.set_ylabel('Unused Gt Mask \nAreas Normalized')
            ax.set_xlabel("Center Distance")
        elif hist_key == "center_distance_vs_unused_pred_mask_area_scatter":
            ax.plot(data["center_distances"][0], data["unused_pred_mask_areas_normalized"][0], ".")
            ax.set_ylabel('Unused Pred Mask \nAreas Normalized')
            ax.set_xlabel("Center Distance")

    def plot_additional_stats_matplotlib(self, class_data, class_name):
        # histograms
        ious = sorted([iou for iou in class_data.keys() if iou != "ap"])
        iou_selector = pnw.Select(name="IOU", options=ious, value=0.5)

        @pn.depends(iou_selector.param.value)
        def _plot_additional_stats_matplotlib(iou):
            nonlocal class_data
            nonlocal self
            data = class_data[iou]
            fig = plt.figure(constrained_layout=False, figsize=(16,9))
            row_coords = self.generate_grid_coodinates(3)[::-1]
            col_coords = self.generate_grid_coodinates(4)[::-1]
            coord_combinations = list(itertools.product(col_coords, row_coords))

            for index, hist_key in enumerate(
                [
                    'center_distances', 'y_center_offsets', 'x_center_offsets',
                    'used_scatter', 'unused_gt_mask_areas_normalized', 'used_gt_mask_areas_normalized',
                    'unused_scatter', 'center_distances', 'y_center_offsets',
                    'xoffset_vs_yoffset_scatter', 'center_distance_vs_unused_gt_mask_area_scatter', "center_distance_vs_unused_pred_mask_area_scatter",
                ]
            ):
                row_coord = coord_combinations[index][0]
                col_coord = coord_combinations[index][1]
                self.histogramm_plot(fig, data, hist_key, row_coord[0], row_coord[1], col_coord[0], col_coord[1])
            plt.close()
            return pn.pane.Matplotlib(fig, width=self.width)
        return pn.Column(iou_selector, _plot_additional_stats_matplotlib)