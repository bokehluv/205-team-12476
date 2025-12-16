import sys
from io import BytesIO

from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QPixmap, QImage, QMovie, QFontDatabase, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QFileDialog,
    QGroupBox,
    QLineEdit,
)
from PIL import Image

from __feature__ import snake_case, true_property


# Image processing helpers

def pixelate(image, target_size):
    #Creates a pixelated image using LANCZOS and NEAREST resampling.
    orig_width, orig_height = image.size

    # Clamp target_size so we don't go larger than the image itself
    min_dim = min(orig_width, orig_height)
    target_size = max(1, min(target_size, min_dim))

    small_img = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    pixel_art_img = small_img.resize((orig_width, orig_height), resample=Image.Resampling.NEAREST)
    return pixel_art_img


def color_pal_reduce(image, target_colors):
    #Reduces the color palette of an image to a specified number of colors.
    target_colors = max(2, min(target_colors, 256))
    quantized_img = image.quantize(
        colors=target_colors,
        method=Image.ADAPTIVE,
        dither=Image.Dither.FLOYDSTEINBERG,
    )
    return quantized_img.convert("RGB")


def color_bit_reduce(image, target_bits):
    #Reduces color depth of an image to a specified number of bits per channel.
    target_bits = max(1, min(target_bits, 8))

    width, height = image.size

    bitmask = 0
    bitset = 128  # 0x80
    for _ in range(target_bits):
        bitmask |= bitset
        bitset >>= 1

    image = image.convert("RGB")
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            r &= bitmask
            g &= bitmask
            b &= bitmask
            pixels[x, y] = r, g, b

    return image


def apply_pixel_art_pipeline(src_image, pixel_size, palette_colors, bit_depth):
    #Run the full pixel-art pipeline on a given Pillow image
    img = pixelate(src_image, pixel_size)
    img = color_pal_reduce(img, palette_colors)
    img = color_bit_reduce(img, bit_depth)
    return img


# Main Window / UI

class PixelArtCreator(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load Roboto Slab & apply globally
        font_id = QFontDatabase.add_application_font("RobotoSlab-VariableFont_wght.ttf")
        if font_id == -1:
            print("Could not load Roboto Slab font file")
        else:
            families = QFontDatabase.application_font_families(font_id)
            if families:
                font = QFont(families[0], 12)
                self.font = font

        self.title = "Pixel Art Creator"
        self.set_window_title(self.title)
        self.resize(800, 600)

        # Full-resolution and preview images
        self.original_image_full = None
        self.preview_base_image = None
        self.current_image = None

        # Central widget + main layout
        central_widget = QWidget()
        self.set_central_widget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.set_layout(main_layout)

        # TOP: animation + Load button
        top_layout = QHBoxLayout()
        main_layout.add_layout(top_layout)

        self.heart_label = QLabel()
        self.heart_label.alignment = Qt.AlignCenter
        self.heart_label.minimum_size = QSize(48, 48)
        self.heart_label.scaled_contents = True

        self.heart_movie = QMovie("animation.gif")
        if self.heart_movie.is_valid():
            self.heart_movie.loop_count = -1
            self.heart_label.set_movie(self.heart_movie)
            self.heart_movie.start()
        else:
            self.heart_label.text = "GIF missing"

        top_layout.add_widget(self.heart_label)

        # Pink load button with Roboto font
        self.load_button = QPushButton("Load Image")
        self.load_button.style_sheet = """
            QPushButton {
                background-color: #eaa7bd;
                color: white;
                border-radius: 10px;
                padding: 6px 12px;
                border-width: 2px;
                border-style: solid;
                border-color: #ff99c2 #c2185b #c2185b #ff99c2;
                font-family: 'Roboto Slab';
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #ff4081;
            }
            QPushButton:pressed {
                background-color: #c2185b;
                border-color: #c2185b #ff99c2 #ff99c2 #c2185b;
            }
        """
        self.load_button.minimum_width = 120
        self.load_button.clicked.connect(self.load_image)
        top_layout.add_widget(self.load_button, stretch=1)

        # MIDDLE: Image display + RIGHT controls
        middle_layout = QHBoxLayout()

        # Image preview area
        self.image_label = QLabel()
        self.image_label.alignment = Qt.AlignCenter
        self.image_label.text = "No image loaded"
        self.image_label.minimum_size = QSize(400, 400)
        self.image_label.style_sheet = """
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 4px;
                font-family: 'Roboto Slab';
            }
        """
        middle_layout.add_widget(self.image_label)

        # Controls group
        right_controls_group = QGroupBox("Controls")
        right_controls_group.style_sheet = """
            QGroupBox {
                font-family: 'Roboto Slab';
                font-size: 13pt;
                font-weight: bold;
            }
        """
        right_controls_layout = QVBoxLayout()
        right_controls_group.set_layout(right_controls_layout)
        right_controls_group.maximum_width = 220

        # PIXEL SIZE controls
        pixelation_layout = QVBoxLayout()

        pixelation_label = QLabel("Pixel Size (resolution):")
        pixelation_label.style_sheet = """
            QLabel {
                font-weight: bold;
                font-family: 'Roboto Slab';
            }
        """

        self.pixelation_up_button = QPushButton("▲")
        self.pixelation_up_button.style_sheet = "QPushButton { font-family: 'Roboto Slab'; }"
        self.pixelation_up_button.clicked.connect(
            lambda: self.increment_slider(self.pixelation_slider, 1)
        )
        self.pixelation_up_button.maximum_width = 50

        self.pixelation_value_label = QLabel("128")
        self.pixelation_value_label.alignment = Qt.AlignCenter
        self.pixelation_value_label.style_sheet = """
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                font-family: 'Roboto Slab';
            }
        """

        self.pixelation_down_button = QPushButton("▼")
        self.pixelation_down_button.style_sheet = "QPushButton { font-family: 'Roboto Slab'; }"
        self.pixelation_down_button.clicked.connect(
            lambda: self.increment_slider(self.pixelation_slider, -1)
        )
        self.pixelation_down_button.maximum_width = 50

        self.pixelation_slider = QSlider(Qt.Vertical)
        self.pixelation_slider.minimum = 8
        self.pixelation_slider.maximum = 256
        self.pixelation_slider.value = 128
        self.pixelation_slider.valueChanged.connect(self.update_preview)

        self.pixelation_input = QLineEdit("128")
        self.pixelation_input.style_sheet = "QLineEdit { font-family: 'Roboto Slab'; }"
        self.pixelation_input.maximum_width = 60
        self.pixelation_input.alignment = Qt.AlignCenter
        self.pixelation_input.returnPressed.connect(
            lambda: self.update_from_text_input(
                self.pixelation_input, self.pixelation_slider, 8, 256
            )
        )

        pixelation_layout.add_widget(pixelation_label)
        pixelation_layout.add_widget(self.pixelation_up_button, alignment=Qt.AlignCenter)
        pixelation_layout.add_widget(self.pixelation_value_label)
        pixelation_layout.add_widget(self.pixelation_down_button, alignment=Qt.AlignCenter)
        pixelation_layout.add_widget(self.pixelation_slider)
        pixelation_layout.add_widget(self.pixelation_input, alignment=Qt.AlignCenter)

        right_controls_layout.add_layout(pixelation_layout)

        # BIT DEPTH controls
        bitdepth_layout = QVBoxLayout()

        bitdepth_label = QLabel("Bit Depth (per channel):")
        bitdepth_label.style_sheet = """
            QLabel {
                font-weight: bold;
                font-family: 'Roboto Slab';
            }
        """

        self.bitdepth_up_button = QPushButton("▲")
        self.bitdepth_up_button.style_sheet = "QPushButton { font-family: 'Roboto Slab'; }"
        self.bitdepth_up_button.clicked.connect(
            lambda: self.increment_slider(self.bitdepth_slider, 1)
        )
        self.bitdepth_up_button.maximum_width = 50

        self.bitdepth_value_label = QLabel("8")
        self.bitdepth_value_label.alignment = Qt.AlignCenter
        self.bitdepth_value_label.style_sheet = """
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                font-family: 'Roboto Slab';
            }
        """

        self.bitdepth_down_button = QPushButton("▼")
        self.bitdepth_down_button.style_sheet = "QPushButton { font-family: 'Roboto Slab'; }"
        self.bitdepth_down_button.clicked.connect(
            lambda: self.increment_slider(self.bitdepth_slider, -1)
        )
        self.bitdepth_down_button.maximum_width = 50

        self.bitdepth_slider = QSlider(Qt.Vertical)
        self.bitdepth_slider.minimum = 1
        self.bitdepth_slider.maximum = 8
        self.bitdepth_slider.value = 8
        self.bitdepth_slider.valueChanged.connect(self.update_preview)

        self.bitdepth_input = QLineEdit("8")
        self.bitdepth_input.style_sheet = "QLineEdit { font-family: 'Roboto Slab'; }"
        self.bitdepth_input.maximum_width = 60
        self.bitdepth_input.alignment = Qt.AlignCenter
        self.bitdepth_input.returnPressed.connect(
            lambda: self.update_from_text_input(
                self.bitdepth_input, self.bitdepth_slider, 1, 8
            )
        )

        bitdepth_layout.add_widget(bitdepth_label)
        bitdepth_layout.add_widget(self.bitdepth_up_button, alignment=Qt.AlignCenter)
        bitdepth_layout.add_widget(self.bitdepth_value_label)
        bitdepth_layout.add_widget(self.bitdepth_down_button, alignment=Qt.AlignCenter)
        bitdepth_layout.add_widget(self.bitdepth_slider)
        bitdepth_layout.add_widget(self.bitdepth_input, alignment=Qt.AlignCenter)

        right_controls_layout.add_layout(bitdepth_layout)

        # Add right controls to middle layout
        middle_layout.add_widget(right_controls_group)
        main_layout.add_layout(middle_layout)

        # COLOR PALETTE section
        palette_group = QGroupBox("Color Palette")
        palette_group.style_sheet = """
            QGroupBox {
                font-family: 'Roboto Slab';
                font-size: 13pt;
                font-weight: bold;
            }
        """

        palette_layout = QHBoxLayout()
        palette_group.set_layout(palette_layout)

        palette_label = QLabel("Number of colors:")
        palette_label.style_sheet = """
            QLabel {
                font-weight: bold;
                font-family: 'Roboto Slab';
            }
        """

        self.palette_left_button = QPushButton("◀")
        self.palette_left_button.style_sheet = "QPushButton { font-family: 'Roboto Slab'; }"
        self.palette_left_button.clicked.connect(
            lambda: self.increment_slider(self.palette_slider, -1)
        )
        self.palette_left_button.maximum_width = 50

        self.palette_slider = QSlider(Qt.Horizontal)
        self.palette_slider.minimum = 2
        self.palette_slider.maximum = 256
        self.palette_slider.value = 128
        self.palette_slider.valueChanged.connect(self.update_preview)

        self.palette_right_button = QPushButton("▶")
        self.palette_right_button.style_sheet = "QPushButton { font-family: 'Roboto Slab'; }"
        self.palette_right_button.clicked.connect(
            lambda: self.increment_slider(self.palette_slider, 1)
        )
        self.palette_right_button.maximum_width = 50

        self.palette_value_label = QLabel("128")
        self.palette_value_label.style_sheet = "QLabel { font-family: 'Roboto Slab'; }"

        self.palette_input = QLineEdit("128")
        self.palette_input.style_sheet = "QLineEdit { font-family: 'Roboto Slab'; }"
        self.palette_input.maximum_width = 60
        self.palette_input.alignment = Qt.AlignCenter
        self.palette_input.returnPressed.connect(
            lambda: self.update_from_text_input(
                self.palette_input, self.palette_slider, 2, 256
            )
        )

        palette_layout.add_widget(palette_label)
        palette_layout.add_widget(self.palette_left_button)
        palette_layout.add_widget(self.palette_slider)
        palette_layout.add_widget(self.palette_right_button)
        palette_layout.add_widget(self.palette_value_label)
        palette_layout.add_widget(self.palette_input)

        main_layout.add_widget(palette_group)

        # SAVE BUTTON
        self.save_button = QPushButton("Save Pixel Art")
        self.save_button.style_sheet = """
            QPushButton {
                background-color: #eaa7bd;
                color: white;
                border-radius: 10px;
                padding: 6px 12px;
                border-width: 2px;
                border-style: solid;
                border-color: #ff99c2 #c2185b #c2185b #ff99c2;
                font-family: 'Roboto Slab';
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #ff4081;
            }
            QPushButton:pressed {
                background-color: #c2185b;
                border-color: #c2185b #ff99c2 #ff99c2 #c2185b;
            }
        """
        self.save_button = QPushButton("Save Pixel Art")

        # copy the exact same style as the Load button
        self.save_button.style_sheet = self.load_button.style_sheet

        self.save_button.clicked.connect(self.save_image)
        self.save_button.enabled = False  # will be set True in load_image()
        main_layout.add_widget(self.save_button)

    # ---------------- Slots & helpers ----------------

    @Slot()
    def load_image(self):
        #Let the user choose an image file and load it
        file_name, _ = QFileDialog.get_open_file_name(
            self,
            "Open Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)",
        )

        if not file_name:
            return

        # Load full-resolution image (for final save)
        self.original_image_full = Image.open(file_name).convert("RGB")

        # Make a smaller copy for fast preview
        max_dim = 512  # you can tweak this
        w, h = self.original_image_full.size
        scale = min(1.0, max_dim / max(w, h))
        if scale < 1.0:
            new_size = (int(w * scale), int(h * scale))
            self.preview_base_image = self.original_image_full.resize(
                new_size, resample=Image.Resampling.LANCZOS
            )
        else:
            self.preview_base_image = self.original_image_full.copy()

        self.save_button.enabled = True
        self.update_preview()

    def increment_slider(self, slider, direction):
        #Increment or decrement a slider's value by the specified direction
        new_value = slider.value + direction
        if slider.minimum <= new_value <= slider.maximum:
            slider.value = new_value

    def update_from_text_input(self, text_input, slider, min_val, max_val):
        #Update slider value from text input with simple validation
        try:
            value = int(text_input.text)
        except ValueError:
            text_input.text = str(slider.value)
            return

        if min_val <= value <= max_val:
            slider.value = value
        else:
            text_input.text = str(slider.value)

    @Slot()
    def update_preview(self):
        #Rebuild the pixel-art preview when any control changes
        if self.preview_base_image is None:
            self.image_label.text = "Load an image to see the preview."
            return

        pixel_size = self.pixelation_slider.value
        palette_colors = self.palette_slider.value
        bit_depth = self.bitdepth_slider.value

        # Update labels + text boxes
        self.pixelation_value_label.text = str(pixel_size)
        self.palette_value_label.text = str(palette_colors)
        self.bitdepth_value_label.text = str(bit_depth)

        self.pixelation_input.text = str(pixel_size)
        self.palette_input.text = str(palette_colors)
        self.bitdepth_input.text = str(bit_depth)

        # Run pipeline on the *small* preview image
        processed_image = apply_pixel_art_pipeline(
            self.preview_base_image,
            pixel_size,
            palette_colors,
            bit_depth,
        )

        self.current_image = processed_image

        # Convert Pillow image -> QPixmap
        buffer = BytesIO()
        processed_image.save(buffer, format="PNG")
        buffer.seek(0)

        qimage = QImage()
        qimage.load_from_data(buffer.read())
        if qimage.is_null():
            self.image_label.text = "Error loading preview."
            return

        pixmap = QPixmap.from_image(qimage)

        scaled_pixmap = pixmap.scaled(
            self.image_label.size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.pixmap = scaled_pixmap

    @Slot()
    def save_image(self):
        #Allow user to save a full-resolution pixel-art image
        if self.original_image_full is None:
            return

        file_name, _ = QFileDialog.get_save_file_name(
            self,
            "Save Pixel Art",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg)",
        )
        if not file_name:
            return

        # Use full-res image for final output (can be slower, but only once)
        pixel_size = self.pixelation_slider.value
        palette_colors = self.palette_slider.value
        bit_depth = self.bitdepth_slider.value

        final_image = apply_pixel_art_pipeline(
            self.original_image_full,
            pixel_size,
            palette_colors,
            bit_depth,
        )
        final_image.save(file_name)


# Run the app

if __name__ == "__main__":
    my_app = QApplication(sys.argv)
    window = PixelArtCreator()
    window.style_sheet = "background-color: #8d749d;"
    window.show()
    sys.exit(my_app.exec())
