# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/components.ipynb (unless otherwise specified).

__all__ = ['gallery', 'barplot_class_occurance', 'area_histogram', 'comparison_histogram_with_gui']

# Cell
from typing import Optional, Union

from icevision.core.class_map import ClassMap

import panel as pn
import panel.widgets as pnw
from bokeh.plotting import figure
import numpy as np
import pandas as pd

from .utils import *

# Cell
def gallery(
    records,
    class_map: Optional[ClassMap] = None,
    display_label: bool = True,
    display_bbox: bool = True,
    display_mask: bool = True,
    display_keypoints: bool = True,
    width=None,
    height=None
):
    """Shows a gallery for a list of records."""
    # gui
    btn_prev = pnw.Button(name="<")
    btn_next = pnw.Button(name=">")
    current = pnw.TextInput(value="1")
    overall = pn.Row("/" + str(len(records)))
    gui = pn.Row(btn_prev, current, overall, btn_next, align="center", height=50)

    # plotting function
    @pn.depends(current.param.value)
    def _plot(_):
        nonlocal current
        try:
            index = int(current.value) - 1
        except:
            pass
        img  = draw_record_with_bokeh(
            record=records[index],
            class_map=class_map,
            display_label=display_label,
            display_bbox=display_bbox,
            display_mask=display_mask,
            display_keypoints=display_keypoints,
            return_figure=True,
            width=width,
            height=height-50 if height is not None else height
        )
        return img

    # add interactions
    def _next(_):
        nonlocal current
        nonlocal records
        try:
            index = int(current.value)
            if index == len(records):
                index = 1
            else:
                index += 1
            current.value = str(index)
        except:
            pass


    def _previous(_):
        nonlocal current
        nonlocal records
        try:
            index = int(current.value)
            if index == 1:
                index = len(records)
            else:
                index -= 1
            current.value = str(index)
        except:
            pass

    btn_prev.on_click(_previous)
    btn_next.on_click(_next)

    return pn.Column(gui, pn.Row(_plot, align="center"))

# Cell
def barplot_class_occurance(record_stats, class_map=None, width=500, height=500):
    """Creates a barplot of the class occurances."""
    result = record_stats.groupby("label").count()["id"]
    counts, values = result.values, result.index.tolist()
    # sort result in decending order
    fig = barplot(counts, values, class_map=class_map, width=width, height=height)
    return pn.Column(fig)

# Cell
def area_histogram(record_stats, class_label, class_map=None, bins=10, normalized=False, density=False, range=None, width=500, height=500):
    """Creates a histogram for a given class_label from record_stats."""
    if normalized:
        df_col = "area_normalized"
        x_label = "Area (normalized)"
    else:
        df_col = "area"
        x_label = "Area"
    if class_map is not None:
        key = class_map.get_id(class_label)
        title = f"{class_map.get_id(class_label)}: {record_stats[record_stats['label'] == class_label].size} objects"
    else:
        title = f"{class_label}: {record_stats[record_stats['label'] == class_label].size} objects"

    p = figure(width=width, height=height, x_axis_label = x_label, y_axis_label = "No. annotations", title=title)
    p = histogram(record_stats[record_stats["label"] == class_label][df_col].values, density=density, bins=bins, range=range, plot_figure=p, width=500, height=500)
    return p

# Cell
def comparison_histogram_with_gui(record_stats_list, hist_func, class_map=None, width=500, height=500):
    """Creates histograms for a list of record_stats and a histogram function (based on the histogram function from utils) with a full gui to customize the histogram parameters.
    The hist function must have the following call head: (record_stats, class_label, class_map, bins, normalized, density, range, width, height)"""
    # gui
    # remove the first entry from the class_map, because the background class is not explicit part of the annotaitons
    unique_labels = sorted(pd.unique(record_stats_list[0]["label"]))
    for record_stats in record_stats_list[1:]:
        if not all(pd.unique(sorted(record_stats["label"])) == unique_labels):
            raise ValueError("All dataframes in the records_stats_list need to have the same set of unique values.")
    options = pd.unique(record_stats_list[0]["label"])
    options.sort()
    if class_map is not None:
        options = np.vectorize(class_map.get_id)(options)
    class_dropdown = pnw.Select(options=options.tolist())

    bins_slider = pnw.IntSlider(name="Bins", start=10, end=100, step=5)
    checkbox_normalized = pnw.Checkbox(name="Normalized", value=False)
    checkbox_density = pnw.Checkbox(name="Density", value=False)

    range_min = int(min(record_stats["area"].min() for record_stats in record_stats_list))
    range_max = int(max(record_stats["area"].max() for record_stats in record_stats_list))
    steps = (range_max-range_min)/50
    range_slider = pnw.RangeSlider(name="Range", start=range_min, end=range_max, step=steps)

    @pn.depends(class_dropdown.param.value, bins_slider.param.value, checkbox_normalized.param.value, checkbox_density.param.value, range_slider.param.value)
    def _draw_histogram(class_label, bins, normalized, density, range):
        nonlocal class_map
        nonlocal width
        nonlocal height
        nonlocal record_stats_list
        class_label = class_label if class_map is None else class_map.get_name(class_label)
        # make the range slider dynamic with respect to the normalization
        if normalized:
            if range_slider.end != 1:
                old_slider_end = range_slider.end
                old_slider_start = range_slider.start
                range_slider.start = 0
                range_slider.end = 1
                range_slider.step = 1/50
                range_slider.value = ((range_slider.value[0]-old_slider_start)/(old_slider_end-old_slider_start), (range_slider.value[1]-old_slider_start)/(old_slider_end-old_slider_start))
                range = range_slider.value
        else:
            if range_slider.end != int(max(record_stats["area"].max() for record_stats in record_stats_list)):
                range_slider.start = int(min(record_stats["area"].min() for record_stats in record_stats_list))
                range_slider.end = int(max(record_stats["area"].max() for record_stats in record_stats_list))
                range_slider.step = (range_max-range_min)/50
                range_slider.value = ((range_slider.value[0]*(range_slider.end-range_slider.start))+range_slider.start, (range_slider.value[1]*(range_slider.end-range_slider.start))+range_slider.start)
                range = range_slider.value
        return pn.Row(*[hist_func(record_stats, class_label, class_map=class_map, bins=bins, normalized=normalized, density=density, range=range, width=width, height=height) for record_stats in record_stats_list])

    return pn.Column(class_dropdown, pn.Row(bins_slider, checkbox_normalized), pn.Row(range_slider, checkbox_density), _draw_histogram)