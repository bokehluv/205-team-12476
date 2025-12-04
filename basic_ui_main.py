import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap


class PixelArtUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pixel Art Creator")
        self.setMinimumSize(600, 500)

        #ALSO DOWNLOADING PyQt5 is required in your enviornment for this code to run
        #UI

        # Image preview
        self.image_label = QLabel("Image preview here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(400, 400)

        # Load button
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(8)
        self.slider.setValue(4)

        # Slider Label
        self.bits_label = QLabel("Bits: 4")
        self.bits_label.setAlignment(Qt.AlignCenter)

        self.slider.valueChanged.connect(self.slider_changed)

        #layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.load_button)
        top_layout.addWidget(self.bits_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(self.slider)

        self.setLayout(main_layout)

        # Store loaded image path (process later)
        self.loaded_image_path = None

    #PLACEHOLDERS--

    def load_image(self):
        """UI only: load image and show it. No processing."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )

        if not file_name:
            return

        self.loaded_image_path = file_name

        # Display orignal image
        pixmap = QPixmap(file_name)
        pixmap = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(pixmap)

        #add algorithm when teammate is ready

    def slider_changed(self, value):
        """UI only: updates displayed number. No processing."""
        self.bits_label.setText(f"Bits: {value}")

        #send slider value to algorithm teammate function


def main():
    app = QApplication(sys.argv)
    window = PixelArtUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

