# sys module needed for optional command line arguments
import sys

# Qt Widgets Module provides a set of UI elements to create classic desktop-style user interfaces
# QApplication is a class in the Qt Widgets module and manages the GUI application's control flow and main settings
# QWidget is a class in the Qt Widgets module and is the base class of all user interface objects
# QLabel is a class in the Qt Widgets module that provides a text or image display
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton


# All other Qt modules rely on this Qt Core
# Qt namespace, used here for GlobalColor enum
# see http://bit.ly/3l6enCh
from PySide6.QtCore import Qt, QSize

from __feature__ import snake_case, true_property # type: ignore


#Task 3

# calls the constructor of the C++ class QApplication
# uses sys.argv to initialize the QT application
# for this application it will pass ['background.py']
my_qt_app = QApplication([])

class task3_window(QWidget):
    def __init__(self):
        super().__init__()
        self.window_title = "Image Display App"
        self.resize(800, 600)

        # Create main layout
        layout = QVBoxLayout()

        # Create a label for displaying image
        self.image_label = QLabel()
        self.image_label.alignment = Qt.AlignmentFlag.AlignCenter
        self.image_label.text = "No image loaded"
        self.image_label.set_style_sheet("border: 2px solid gray; background-color: lightgray;")
        # self.image_label.set_minimum_size(400, 400)

        # Create upload button
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.file_upload_on_click)

        # Create another button
        self.my_button = QPushButton("Press Me")
        self.my_button.clicked.connect(self.on_click2)

        # Create label for messages
        self.my_lbl = QLabel("Welcome!")
        self.my_lbl.alignment = Qt.AlignmentFlag.AlignCenter

        # Add widgets to layout
        layout.add_widget(self.upload_button)
        layout.add_widget(self.image_label)
        layout.add_widget(self.my_button)
        layout.add_widget(self.my_lbl)

        self.set_layout(layout)
    
    def on_click1(self):
        self.my_lbl.text = "Yay Thank you!"
    
    def on_click2(self):
        self.my_lbl.text = "OH GOD YOU PUSHED ME IT HURTS"
        
    def file_upload_on_click(self):
        self.my_lbl.text = "File uploaded"

my_window = task3_window()
my_window.show()

# my_qt_app.exec_() runs the main loop
# putting it in sys.exit() allows for a graceful exit
sys.exit(my_qt_app.exec())


# Task 2:
# PySide6.QtWidgets.QGraphicsGridLayout
#This widget provides a grid layout for managing Widgets in a graphic view
