# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils.ipynb (unless otherwise specified).

__all__ = ['erles_to_string', 'erles_to_counts_to_utf8', 'string_to_erles', 'correct_mask']

# Cell
import json
from copy import deepcopy
import numpy as np
from PIL import Image

from icevision.core.mask import EncodedRLEs, MaskArray

from pycocotools import mask as mask_utils

# Cell
def erles_to_string(erles):
    erles_copy = deepcopy(erles)
    erles_copy["counts"] = erles_copy["counts"].decode("utf-8")
    return json.dumps(erles_copy)

# Cell
def erles_to_counts_to_utf8(erles):
    erles_copy = deepcopy(erles)
    for entry in erles_copy:
        entry["counts"] = entry["counts"].decode("utf-8")
    return erles_copy

# Cell
def string_to_erles(erles_string):
    erles = json.loads(erles_string)
    erles["counts"] = erles["counts"].encode()
    return erles

# Cell
def correct_mask(mask_array, pad_x, pad_y, width, height):
    # correct mask
    corrected_mask_array = mask_array.transpose(2, 0, 1)
    if round(pad_x/2) > 0:
        corrected_mask_array=corrected_mask_array[:,:,round(pad_x/2):round(-pad_x/2)]
    if round(pad_y/2) > 0:
        corrected_mask_array=corrected_mask_array[:,round(pad_y/2):round(-pad_y/2),:]
    corrected_mask_array = np.array(Image.fromarray(corrected_mask_array[0,:,:]).resize([width, height], Image.NEAREST))
    corrected_mask_array = np.expand_dims(corrected_mask_array, 0)
    # convert mask array to mask and get erles (only one erles exist!)
    corrected_mask = MaskArray(corrected_mask_array)
    return corrected_mask