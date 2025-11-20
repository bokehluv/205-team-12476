from PIL import Image
import numpy as np

img = Image.open("test_images/cat2.jpg").convert("RGB")
# img.show()

#Creates a pixelated image using LANCZOS and NEAREST resampling methods
#param image: Pillow image object
#param target_size: The "pixel size" of the pixelated image
def pixelate(image, target_size):
    
    orig_width, orig_height = img.size
    
    small_img = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    
    pixel_art_img = small_img.resize((orig_width, orig_height), resample=Image.Resampling.NEAREST)
    
    pixel_art_img.show()
            
    

pixelate(img, 16) #test