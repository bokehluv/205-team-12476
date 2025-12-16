import sys
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, Slot, QUrl
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
from PySide6.QtQuickWidgets import QQuickWidget
from PIL import Image


# --- Pixel art algorithms (same as your original script) --------------------


def pixelate(image, target_size: int) -> Image.Image:
    orig_width, orig_height = image.size
    small_img = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    pixel_art_img = small_img.resize((orig_width, orig_height), resample=Image.Resampling.NEAREST)
    return pixel_art_img


def color_pal_reduce(image, target_colors: int) -> Image.Image:
    quantized_img = image.quantize(
        colors=target_colors,
        method=Image.ADAPTIVE,
        dither=Image.Dither.FLOYDSTEINBERG,
    )
    return quantized_img.convert("RGB")


def color_bit_reduce(image, target_bits: int) -> Image.Image:
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
            pixels[x, y] = (r, g, b)

    return image


# --- Main window with QML comparison ----------------------------------------


class PixelArtCreator(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Pixel Art Creator")
        self.resize(800, 600)

        self.original_image: Image.Image | None = None
        self.current_image: Image.Image | None = None

        # Temp files for before/after that the QML will load
        self._temp_original = os.path.join(tempfile.gettempdir(), "pixelart_before.png")
        self._temp_processed = os.path.join(tempfile.gettempdir(), "pixelart_after.png")

        # QML component path (ImageComparison.qml must be in the same folder)
        self._comparison_qml = QUrl.fromLocalFile(
            str(Path(__file__).with_name("ImageComparison.qml"))
        )

        # --- Layouts ---------------------------------------------------------
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Load button
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        main_layout.addWidget(self.load_button)

        # Middle layout: QML comparison + right-side controls
        middle_layout = QHBoxLayout()
        main_layout.addLayout(middle_layout)

        # QML comparison widget (before/after slider)
        self.image_comparison = QQuickWidget()
        self.image_comparison.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.image_comparison.setSource(self._comparison_qml)
        self.image_comparison.setClearColor(Qt.black)
        middle_layout.addWidget(self.image_comparison, stretch=1)

        # Right controls group
        right_group = QGroupBox("Controls")
        right_layout = QVBoxLayout()
        right_group.setLayout(right_layout)
        right_group.setMaximumWidth(200)
        middle_layout.addWidget(right_group)

        # --- Pixelation controls --------------------------------------------
        pixelation_layout = QVBoxLayout()
        pixelation_label = QLabel("Pixel Size:")

        self.pixelation_up_button = QPushButton("▲")
        self.pixelation_up_button.setMaximumWidth(50)
        self.pixelation_up_button.clicked.connect(
            lambda: self.increment_slider(self.pixelation_slider, 1)
        )

        self.pixelation_value_label = QLabel("128")
        self.pixelation_value_label.setAlignment(Qt.AlignCenter)
        self.pixelation_value_label.setStyleSheet(
            "QLabel { font-size: 18pt; font-weight: bold; }"
        )

        self.pixelation_down_button = QPushButton("▼")
        self.pixelation_down_button.setMaximumWidth(50)
        self.pixelation_down_button.clicked.connect(
            lambda: self.increment_slider(self.pixelation_slider, -1)
        )

        self.pixelation_slider = QSlider(Qt.Vertical)
        self.pixelation_slider.setMinimum(8)
        self.pixelation_slider.setMaximum(256)
        self.pixelation_slider.setValue(128)
        self.pixelation_slider.valueChanged.connect(self.update_preview)

        self.pixelation_input = QLineEdit("128")
        self.pixelation_input.setMaximumWidth(60)
        self.pixelation_input.setAlignment(Qt.AlignCenter)
        self.pixelation_input.returnPressed.connect(
            lambda: self.update_from_text_input(
                self.pixelation_input, self.pixelation_slider, 8, 256
            )
        )

        pixelation_layout.addWidget(pixelation_label)
        pixelation_layout.addWidget(self.pixelation_up_button, alignment=Qt.AlignCenter)
        pixelation_layout.addWidget(self.pixelation_value_label)
        pixelation_layout.addWidget(self.pixelation_down_button, alignment=Qt.AlignCenter)
        pixelation_layout.addWidget(self.pixelation_slider)
        pixelation_layout.addWidget(self.pixelation_input, alignment=Qt.AlignCenter)
        right_layout.addLayout(pixelation_layout)

        # --- Bit depth controls ---------------------------------------------
        bitdepth_layout = QVBoxLayout()
        bitdepth_label = QLabel("Bit Depth:")

        self.bitdepth_up_button = QPushButton("▲")
        self.bitdepth_up_button.setMaximumWidth(50)
        self.bitdepth_up_button.clicked.connect(
            lambda: self.increment_slider(self.bitdepth_slider, 1)
        )

        self.bitdepth_value_label = QLabel("8")
        self.bitdepth_value_label.setAlignment(Qt.AlignCenter)
        self.bitdepth_value_label.setStyleSheet(
            "QLabel { font-size: 18pt; font-weight: bold; }"
        )

        self.bitdepth_down_button = QPushButton("▼")
        self.bitdepth_down_button.setMaximumWidth(50)
        self.bitdepth_down_button.clicked.connect(
            lambda: self.increment_slider(self.bitdepth_slider, -1)
        )

        self.bitdepth_slider = QSlider(Qt.Vertical)
        self.bitdepth_slider.setMinimum(1)
        self.bitdepth_slider.setMaximum(8)
        self.bitdepth_slider.setValue(8)
        self.bitdepth_slider.valueChanged.connect(self.update_preview)

        self.bitdepth_input = QLineEdit("8")
        self.bitdepth_input.setMaximumWidth(60)
        self.bitdepth_input.setAlignment(Qt.AlignCenter)
        self.bitdepth_input.returnPressed.connect(
            lambda: self.update_from_text_input(
                self.bitdepth_input, self.bitdepth_slider, 1, 8
            )
        )

        bitdepth_layout.addWidget(bitdepth_label)
        bitdepth_layout.addWidget(self.bitdepth_up_button, alignment=Qt.AlignCenter)
        bitdepth_layout.addWidget(self.bitdepth_value_label)
        bitdepth_layout.addWidget(self.bitdepth_down_button, alignment=Qt.AlignCenter)
        bitdepth_layout.addWidget(self.bitdepth_slider)
        bitdepth_layout.addWidget(self.bitdepth_input, alignment=Qt.AlignCenter)
        right_layout.addLayout(bitdepth_layout)

        # --- Palette controls (bottom) --------------------------------------
        palette_group = QGroupBox("Color Palette")
        palette_layout = QHBoxLayout()
        palette_group.setLayout(palette_layout)

        palette_label = QLabel("Colors:")

        self.palette_left_button = QPushButton("◀")
        self.palette_left_button.setMaximumWidth(50)
        self.palette_left_button.clicked.connect(
            lambda: self.increment_slider(self.palette_slider, -1)
        )

        self.palette_slider = QSlider(Qt.Horizontal)
        self.palette_slider.setMinimum(2)
        self.palette_slider.setMaximum(256)
        self.palette_slider.setValue(128)
        self.palette_slider.valueChanged.connect(self.update_preview)

        self.palette_right_button = QPushButton("▶")
        self.palette_right_button.setMaximumWidth(50)
        self.palette_right_button.clicked.connect(
            lambda: self.increment_slider(self.palette_slider, 1)
        )

        self.palette_value_label = QLabel("128")

        self.palette_input = QLineEdit("128")
        self.palette_input.setMaximumWidth(60)
        self.palette_input.setAlignment(Qt.AlignCenter)
        self.palette_input.returnPressed.connect(
            lambda: self.update_from_text_input(
                self.palette_input, self.palette_slider, 2, 256
            )
        )

        palette_layout.addWidget(palette_label)
        palette_layout.addWidget(self.palette_left_button)
        palette_layout.addWidget(self.palette_slider)
        palette_layout.addWidget(self.palette_right_button)
        palette_layout.addWidget(self.palette_value_label)
        palette_layout.addWidget(self.palette_input)

        main_layout.addWidget(palette_group)

        # Save button
        self.save_button = QPushButton("Save Pixel Art")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)
        main_layout.addWidget(self.save_button)

    # ------------------------------------------------------------------ #
    # Slots / logic                                                      #
    # ------------------------------------------------------------------ #

    @Slot()
    def load_image(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)",
        )
        if file_name:
            self.original_image = Image.open(file_name).convert("RGB")
            self.save_button.setEnabled(True)
            self.update_preview()

    def increment_slider(self, slider: QSlider, direction: int) -> None:
        new_value = slider.value() + direction
        if slider.minimum() <= new_value <= slider.maximum():
            slider.setValue(new_value)

    def update_from_text_input(
        self, text_input: QLineEdit, slider: QSlider, min_val: int, max_val: int
    ) -> None:
        try:
            value = int(text_input.text())
        except ValueError:
            text_input.setText(str(slider.value()))
            return

        if min_val <= value <= max_val:
            slider.setValue(value)
        else:
            text_input.setText(str(slider.value()))

    def _update_qml_comparison(self) -> None:
        if self.original_image is None or self.current_image is None:
            return

        # Save images to temporary files
        self.original_image.save(self._temp_original, format="PNG")
        self.current_image.save(self._temp_processed, format="PNG")

        root = self.image_comparison.rootObject()
        if root is None:
            # If this happens, check the console for QML errors
            return

        left_url = QUrl.fromLocalFile(self._temp_original).toString()
        right_url = QUrl.fromLocalFile(self._temp_processed).toString()

        root.setProperty("leftSource", left_url)
        root.setProperty("rightSource", right_url)

    @Slot()
    def update_preview(self) -> None:
        if self.original_image is None:
            return

        pixel_size = self.pixelation_slider.value()
        palette_colors = self.palette_slider.value()
        bit_depth = self.bitdepth_slider.value()

        # Sync labels and text boxes
        self.pixelation_value_label.setText(str(pixel_size))
        self.palette_value_label.setText(str(palette_colors))
        self.bitdepth_value_label.setText(str(bit_depth))

        self.pixelation_input.setText(str(pixel_size))
        self.palette_input.setText(str(palette_colors))
        self.bitdepth_input.setText(str(bit_depth))

        # Apply effects
        processed_image = pixelate(self.original_image, pixel_size)
        processed_image = color_pal_reduce(processed_image, palette_colors)
        processed_image = color_bit_reduce(processed_image, bit_depth)

        self.current_image = processed_image

        # Push images into QML comparison
        self._update_qml_comparison()

    @Slot()
    def save_image(self) -> None:
        if self.current_image is None:
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Pixel Art",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg)",
        )
        if file_name:
            self.current_image.save(file_name)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PixelArtCreator()
    window.show()
    sys.exit(app.exec())
