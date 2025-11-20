
from PIL import Image, ImageStat
import numpy as np
import time


img = Image.open("test_images/cat2.jpg").convert("RGB")
## img.show()

#Creates a pixelated image using LANCZOS and NEAREST resampling methods
#param image: Pillow image object
#param target_size: The "pixel size" of the pixelated image

def pixelate(image, target_size):
    orig_width, orig_height = image.size
    small_img = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    pixel_art_img = small_img.resize((orig_width, orig_height), resample=Image.Resampling.NEAREST)
    pixel_art_img.save("test_images/pixelated_cat2.png")
    return pixel_art_img

#CREDITS TO GEMINI FOR EXAMPLE
def manual_pixel_grid_method(input_path, output_path, target_size):
    # 1. Open the image
    img = Image.open(input_path).convert("RGB")
    width, height = img.size
    
    # 2. Create a blank canvas for the small "pixel" version
    # This acts as the "smaller image" you mentioned
    small_img = Image.new("RGB", (target_size, target_size))
    pixels = small_img.load() # Create a pixel map to edit directly
    
    # 3. Calculate how big our blocks are
    # For 1000px / 64, the block_x is approx 15.625
    block_x = width / target_size
    block_y = height / target_size
    
    print("Processing blocks...")
    
    # 4. Loop through every "target" pixel (0 to 63)
    for x in range(target_size):
        for y in range(target_size):
            
            # Calculate the coordinates in the original high-res image
            # We use int() to snap to the nearest whole pixel
            left = int(x * block_x)
            upper = int(y * block_y)
            right = int((x + 1) * block_x)
            lower = int((y + 1) * block_y)
            
            # 5. Crop the block from the original image
            # This effectively "grabs the grid of blocks"
            block = img.crop((left, upper, right, lower))
            
            # 6. Calculate the average color of this block
            # ImageStat is a helper to do the math (R+R+R/total, G+G+G/total, etc.)
            stat = ImageStat.Stat(block)
            average_color = stat.mean # Returns [R, G, B] floats
            
            # Convert floats (e.g. 120.5) to integers (120) for the color
            r, g, b = int(average_color[0]), int(average_color[1]), int(average_color[2])
            
            # 7. Paint the pixel onto the small image
            pixels[x, y] = (r, g, b)

    # 8. Upscale back to original size (Nearest Neighbor) so we can see it
    final_result = small_img.resize((width, height), resample=Image.Resampling.NEAREST)
    
    final_result.save(output_path)
    print(f"Done! Saved manually processed image to {output_path}")
    

# Timing the pixelation process
start_time = time.time()

# pixelate(img, 32) #test
manual_pixel_grid_method("test_images/cat2.jpg", "test_images/manual_pixelated_cat2.png", 32)

end_time = time.time()
print(f"Pixelation took {end_time - start_time:.4f} seconds.")