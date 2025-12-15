import sys
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                                QVBoxLayout, QHBoxLayout, QPushButton, 
                                QSlider, QFileDialog, QGroupBox, QLineEdit)
from PIL import Image
from io import BytesIO

from __feature__ import snake_case, true_property


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


class PixelArtCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "Pixel Art Creator"
        self.set_window_title(self.title)
        self.resize(800, 600)
        self.original_image = None
        self.current_image = None
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.set_central_widget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.set_layout(main_layout)

        # Load button
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        main_layout.add_widget(self.load_button)

        # Create horizontal layout for image and right-side controls
        middle_layout = QHBoxLayout()
        
        # Image display
        self.image_label = QLabel()
        self.image_label.alignment = Qt.AlignCenter
        self.image_label.text = "No image loaded"
        self.image_label.minimum_size = QSize(400, 400)
        self.image_label.style_sheet = "QLabel { background-color: #f0f0f0; border: 2px solid #ccc; }"
        middle_layout.add_widget(self.image_label)

        # Right-side controls group
        right_controls_group = QGroupBox("Controls")
        right_controls_layout = QVBoxLayout()
        right_controls_group.set_layout(right_controls_layout)
        right_controls_group.maximum_width = 200

        # Pixelation slider (right side)
        pixelation_layout = QVBoxLayout()
        pixelation_label = QLabel("Pixel Size:")
        
        # Up arrow button
        self.pixelation_up_button = QPushButton("▲")
        self.pixelation_up_button.clicked.connect(lambda: self.increment_slider(self.pixelation_slider, 1))
        self.pixelation_up_button.maximum_width = 50
        
        self.pixelation_value_label = QLabel("128")
        self.pixelation_value_label.alignment = Qt.AlignCenter
        self.pixelation_value_label.style_sheet = "QLabel { font-size: 18pt; font-weight: bold; }"
        
        # Down arrow button
        self.pixelation_down_button = QPushButton("▼")
        self.pixelation_down_button.clicked.connect(lambda: self.increment_slider(self.pixelation_slider, -1))
        self.pixelation_down_button.maximum_width = 50
        
        self.pixelation_slider = QSlider(Qt.Vertical)
        self.pixelation_slider.minimum = 8
        self.pixelation_slider.maximum = 256
        self.pixelation_slider.value = 128
        self.pixelation_slider.valueChanged.connect(self.update_preview)
        
        # Text input box
        self.pixelation_input = QLineEdit("128")
        self.pixelation_input.maximum_width = 60
        self.pixelation_input.alignment = Qt.AlignCenter
        self.pixelation_input.returnPressed.connect(lambda: self.update_from_text_input(self.pixelation_input, self.pixelation_slider, 8, 256))
        
        pixelation_layout.add_widget(pixelation_label)
        pixelation_layout.add_widget(self.pixelation_up_button, alignment=Qt.AlignCenter)
        pixelation_layout.add_widget(self.pixelation_value_label)
        pixelation_layout.add_widget(self.pixelation_down_button, alignment=Qt.AlignCenter)
        pixelation_layout.add_widget(self.pixelation_slider)
        pixelation_layout.add_widget(self.pixelation_input, alignment=Qt.AlignCenter)
        right_controls_layout.add_layout(pixelation_layout)

        # Color bit depth slider (right side)
        bitdepth_layout = QVBoxLayout()
        bitdepth_label = QLabel("Bit Depth:")
        
        # Up arrow button
        self.bitdepth_up_button = QPushButton("▲")
        self.bitdepth_up_button.clicked.connect(lambda: self.increment_slider(self.bitdepth_slider, 1))
        self.bitdepth_up_button.maximum_width = 50
        
        self.bitdepth_value_label = QLabel("8")
        self.bitdepth_value_label.alignment = Qt.AlignCenter
        self.bitdepth_value_label.style_sheet = "QLabel { font-size: 18pt; font-weight: bold; }"
        
        # Down arrow button
        self.bitdepth_down_button = QPushButton("▼")
        self.bitdepth_down_button.clicked.connect(lambda: self.increment_slider(self.bitdepth_slider, -1))
        self.bitdepth_down_button.maximum_width = 50
        
        self.bitdepth_slider = QSlider(Qt.Vertical)
        self.bitdepth_slider.minimum = 1
        self.bitdepth_slider.maximum = 8
        self.bitdepth_slider.value = 8
        self.bitdepth_slider.valueChanged.connect(self.update_preview)
        
        # Text input box
        self.bitdepth_input = QLineEdit("8")
        self.bitdepth_input.maximum_width = 60
        self.bitdepth_input.alignment = Qt.AlignCenter
        self.bitdepth_input.returnPressed.connect(lambda: self.update_from_text_input(self.bitdepth_input, self.bitdepth_slider, 1, 8))
        
        bitdepth_layout.add_widget(bitdepth_label)
        bitdepth_layout.add_widget(self.bitdepth_up_button, alignment=Qt.AlignCenter)
        bitdepth_layout.add_widget(self.bitdepth_value_label)
        bitdepth_layout.add_widget(self.bitdepth_down_button, alignment=Qt.AlignCenter)
        bitdepth_layout.add_widget(self.bitdepth_slider)
        bitdepth_layout.add_widget(self.bitdepth_input, alignment=Qt.AlignCenter)
        right_controls_layout.add_layout(bitdepth_layout)
        
        middle_layout.add_widget(right_controls_group)
        main_layout.add_layout(middle_layout)

        # Color palette slider (bottom)
        palette_group = QGroupBox("Color Palette")
        palette_layout = QHBoxLayout()
        palette_group.set_layout(palette_layout)
        palette_label = QLabel("Colors:")
        
        # Left arrow button
        self.palette_left_button = QPushButton("◀")
        self.palette_left_button.clicked.connect(lambda: self.increment_slider(self.palette_slider, -1))
        self.palette_left_button.maximum_width = 50
        
        self.palette_slider = QSlider(Qt.Horizontal)
        self.palette_slider.minimum = 2
        self.palette_slider.maximum = 256
        self.palette_slider.value = 128
        self.palette_slider.valueChanged.connect(self.update_preview)
        
        # Right arrow button
        self.palette_right_button = QPushButton("▶")
        self.palette_right_button.clicked.connect(lambda: self.increment_slider(self.palette_slider, 1))
        self.palette_right_button.maximum_width = 50
        
        self.palette_value_label = QLabel("128")
        
        # Text input box
        self.palette_input = QLineEdit("128")
        self.palette_input.maximum_width = 60
        self.palette_input.alignment = Qt.AlignCenter
        self.palette_input.returnPressed.connect(lambda: self.update_from_text_input(self.palette_input, self.palette_slider, 2, 256))
        
        palette_layout.add_widget(palette_label)
        palette_layout.add_widget(self.palette_left_button)
        palette_layout.add_widget(self.palette_slider)
        palette_layout.add_widget(self.palette_right_button)
        palette_layout.add_widget(self.palette_value_label)
        palette_layout.add_widget(self.palette_input)
        main_layout.add_widget(palette_group)
        
        # Save button
        self.save_button = QPushButton("Save Pixel Art")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.enabled = False
        main_layout.add_widget(self.save_button)

    @Slot()
    def load_image(self):
        # Ask user for file
        file_name, _ = QFileDialog.get_open_file_name(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        
        if file_name:  # Only load if user selected a file
            self.original_image = Image.open(file_name).convert("RGB")
            self.save_button.enabled = True
            self.update_preview()
    
    def increment_slider(self, slider, direction):
        """Increment or decrement a slider's value by the specified direction"""
        new_value = slider.value + direction
        if new_value >= slider.minimum and new_value <= slider.maximum:
            slider.value = new_value
    
    def update_from_text_input(self, text_input, slider, min_val, max_val):
        """Update slider value from text input with validation"""
        try:
            value = int(text_input.text)
            if value >= min_val and value <= max_val:
                slider.value = value
            else:
                # Reset to current slider value if out of range
                text_input.text = str(slider.value)
        except ValueError:
            # Reset to current slider value if invalid input
            text_input.text = str(slider.value)
    
    @Slot()
    def update_preview(self):
        # Get slider values
        pixel_size = self.pixelation_slider.value
        palette_colors = self.palette_slider.value
        bit_depth = self.bitdepth_slider.value
        
        # Update value labels
        self.pixelation_value_label.text = str(pixel_size)
        self.palette_value_label.text = str(palette_colors)
        self.bitdepth_value_label.text = str(bit_depth)
        
        # Update text input boxes
        self.pixelation_input.text = str(pixel_size)
        self.palette_input.text = str(palette_colors)
        self.bitdepth_input.text = str(bit_depth)
        
        # Apply effects
        processed_image = pixelate(self.original_image, pixel_size)
        processed_image = color_pal_reduce(processed_image, palette_colors)
        processed_image = color_bit_reduce(processed_image, bit_depth)
        
        self.current_image = processed_image
        
        # Convert PIL image to bytes
        buffer = BytesIO()
        processed_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Load into QPixmap
        qimage = QImage()
        qimage.load_from_data(buffer.read())
        pixmap = QPixmap.from_image(qimage)

        # Display image (scale to fit label)
        scaled_pixmap = pixmap.scaled(self.image_label.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.pixmap = scaled_pixmap
    
    @Slot()
    def save_image(self):
        # Allow user to save the result
        file_name, _ = QFileDialog.get_save_file_name(self, "Save Pixel Art", "", "PNG Files (*.png);;JPEG Files (*.jpg)")
        if file_name:
            self.current_image.save(file_name)


# Create application
my_app = QApplication([])
# Create window	
window = PixelArtCreator()
window.show()
# Run Qt program
sys.exit(my_app.exec())