import sys
import time
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                                QVBoxLayout, QHBoxLayout, QPushButton, 
                                QSlider, QFileDialog, QGroupBox)
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
    bitmask = 0
    bitset = 128    # 0x80
    for b in range(target_bits):
        bitmask = bitmask | bitset
        bitset = bitset >> 1
    
    # Optimization: Use a lookup table instead of per-pixel iteration
    lookup_table = [i & bitmask for i in range(256)]
    
    # Ensure RGB and apply table (requires 256 values per channel)
    return image.convert("RGB").point(lookup_table * 3)


# --- Constants ---
STYLESHEET = """
    QMainWindow {
        background-color: #2b2b2b;
    }
    QLabel {
        color: #ffffff;
        font-size: 14px;
    }
    QGroupBox {
        color: #ffffff;
        font-weight: bold;
        border: 1px solid #555;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
    QPushButton {
        background-color: #0d6efd;
        color: white;
        border-radius: 5px;
        padding: 8px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #0b5ed7;
    }
    QPushButton:disabled {
        background-color: #555;
        color: #aaa;
    }
    QSlider::groove:horizontal {
        border: 1px solid #999999;
        height: 8px;
        background: #444;
        margin: 2px 0;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: #0d6efd;
        border: 1px solid #0d6efd;
        width: 18px;
        height: 18px;
        margin: -7px 0;
        border-radius: 9px;
    }
"""

class PixelArtCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_ui()

    def setup_window(self):
        """Sets up the main window properties."""
        self.title = "Pixel Art Creator"
        self.set_window_title(self.title)
        self.resize(1000, 700)
        self.style_sheet = STYLESHEET
        self.original_image = None
        self.current_image = None

    def setup_ui(self):
        """Initializes the user interface layout."""
        central_widget = QWidget()
        self.set_central_widget(central_widget)
        
        # Main layout is horizontal: [Controls] | [Image]
        main_layout = QHBoxLayout()
        central_widget.set_layout(main_layout)

        # Add the two main panels
        main_layout.add_widget(self.create_left_panel())
        main_layout.add_widget(self.create_right_panel())

    def create_left_panel(self):
        """Creates the left sidebar with all controls."""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.set_layout(layout)
        panel.maximum_width = 300
        
        # Title
        title_label = QLabel("Pixel Art Creator")
        title_label.style_sheet = "font-size: 24px; font-weight: bold; color: #0d6efd; margin-bottom: 10px;"
        title_label.alignment = Qt.AlignCenter
        layout.add_widget(title_label)

        # Load Button
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        layout.add_widget(self.load_button)

        # Settings Group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        settings_group.set_layout(settings_layout)

        # Add sliders to settings group
        self.create_slider(settings_layout, "Pixel Size:", 8, 256, 128, "pixelation")
        self.create_slider(settings_layout, "Color Palette:", 2, 256, 128, "palette")
        self.create_slider(settings_layout, "Bit Depth:", 1, 8, 8, "bitdepth")
        
        layout.add_widget(settings_group)
        layout.add_stretch() # Push everything up

        # Save Button
        self.save_button = QPushButton("Save Pixel Art")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.enabled = False
        layout.add_widget(self.save_button)

        return panel

    def create_right_panel(self):
        """Creates the right panel for image display."""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.set_layout(layout)

        self.image_label = QLabel()
        self.image_label.alignment = Qt.AlignCenter
        self.image_label.text = "No image loaded"
        self.image_label.minimum_size = QSize(400, 400)
        self.image_label.style_sheet = "QLabel { background-color: #1e1e1e; border: 2px dashed #444; border-radius: 10px; color: #888; }"
        
        layout.add_widget(self.image_label)
        return panel

    def create_slider(self, parent_layout, label_text, min_val, max_val, default_val, name_prefix):
        """Helper to create a slider with label and value display."""
        layout = QHBoxLayout()
        
        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.minimum = min_val
        slider.maximum = max_val
        slider.value = default_val
        slider.valueChanged.connect(self.update_preview)
        
        value_label = QLabel(str(default_val))
        value_label.alignment = Qt.AlignRight

        # Store references so we can access them later
        setattr(self, f"{name_prefix}_slider", slider)
        setattr(self, f"{name_prefix}_value_label", value_label)

        layout.add_widget(label)
        layout.add_widget(slider)
        layout.add_widget(value_label)
        parent_layout.add_layout(layout)

    @Slot()
    def load_image(self):
        file_name, _ = QFileDialog.get_open_file_name(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.original_image = Image.open(file_name).convert("RGB")
            self.save_button.enabled = True
            self.update_preview()
    
    @Slot()
    def update_preview(self):
        if self.original_image is None:
            return

        start_time = time.time()

        # Get values from sliders
        pixel_size = self.pixelation_slider.value
        palette_colors = self.palette_slider.value
        bit_depth = self.bitdepth_slider.value
        
        # Update labels
        self.pixelation_value_label.text = str(pixel_size)
        self.palette_value_label.text = str(palette_colors)
        self.bitdepth_value_label.text = str(bit_depth)
        
        # Apply effects
        t = time.time()
        processed_image = pixelate(self.original_image, pixel_size)
        # print(f"Pixelate: {time.time() - t:.4f}s")

        t = time.time()
        processed_image = color_pal_reduce(processed_image, palette_colors)
        # print(f"Palette Reduce: {time.time() - t:.4f}s")

        t = time.time()
        processed_image = color_bit_reduce(processed_image, bit_depth)
        # print(f"Bit Reduce: {time.time() - t:.4f}s")
        
        self.current_image = processed_image
        
        # Display image
        self.display_image(processed_image)

        # print(f"Total Time: {time.time() - start_time:.4f}s")

    def display_image(self, image):
        """Converts PIL image to QPixmap and displays it."""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        qimage = QImage()
        qimage.load_from_data(buffer.read())
        pixmap = QPixmap.from_image(qimage)

        scaled_pixmap = pixmap.scaled(self.image_label.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.pixmap = scaled_pixmap
    
    @Slot()
    def save_image(self):
        file_name, _ = QFileDialog.get_save_file_name(self, "Save Pixel Art", "", "PNG Files (*.png);;JPEG Files (*.jpg)")
        if file_name:
            self.current_image.save(file_name)


if __name__ == "__main__":
    app = QApplication([])
    window = PixelArtCreator()
    window.show()
    sys.exit(app.exec())