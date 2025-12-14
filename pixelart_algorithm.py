
from PIL import Image
import numpy as np


#Creates a pixelated image using LANCZOS and NEAREST resampling methods
#param image: Pillow image object
#param target_size: The "pixel size" of the pixelated image
def pixelate(image, target_size):
    orig_width, orig_height = image.size
    small_img = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    pixel_art_img = small_img.resize((orig_width, orig_height), resample=Image.Resampling.NEAREST)
    return pixel_art_img
