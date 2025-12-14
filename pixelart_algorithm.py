
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


#Reduces the color palette of an image to a specified number of colors
#param image: Pillow image object
#param target_size: new size of the image's palette
def color_pal_reduce(image, target_colors):
    quantized_img = image.quantize(colors=target_colors, method=Image.ADAPTIVE, 
                                   dither=Image.Dither.FLOYDSTEINBERG)
    return quantized_img.convert("RGB")


#Reduces color depth of an image to a specified number of bits per channel
#param image: Pillow image object
#param target_size: The number of bits per color
def color_bit_reduce(image, target_bits):
    width, height = image.size
    
    bitmask = 0
    bitset = 128    # 0x80
    for b in range(target_bits):
        bitmask = bitmask | bitset
        bitset = bitset >> 1
    
    image = image.convert("RGB")
    pixels = image.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            r = r & bitmask
            g = g & bitmask
            b = b & bitmask
            pixels[x, y] = r, g, b
    
    return image