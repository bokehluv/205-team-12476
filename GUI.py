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
from PySide6.QtCore import Qt

from __feature__ import snake_case, true_property # type: ignore


#Task 3

# calls the constructor of the C++ class QApplication
# uses sys.argv to initialize the QT application
# for this application it will pass ['background.py']
my_qt_app = QApplication([])

class task3_window(QWidget):
    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout()

        btn = QPushButton('Push me!')
        btn1 = QPushButton('DONT PUSH ME')
        self.my_lbl = QLabel('Buttons!')
        btn.clicked.connect(self.on_click1)
        btn1.clicked.connect(self.on_click2)

        vbox.add_widget(btn)
        vbox.add_widget(btn1)
        vbox.add_widget(self.my_lbl)
        self.window_title = 'Mikey Huntzinger'
        self.set_layout(vbox)
        self.resize(300,300)
        self.palette = Qt.darkMagenta
    
    def on_click1(self):
        self.my_lbl.text = "Yay Thank you!"
    
    def on_click2(self):
        self.my_lbl.text = "OH GOD YOU PUSHED ME IT HURTS"

my_window = task3_window()
my_window.show()

# my_qt_app.exec_() runs the main loop
# putting it in sys.exit() allows for a graceful exit
sys.exit(my_qt_app.exec())


# Task 2:
# PySide6.QtWidgets.QGraphicsGridLayout
#This widget provides a grid layout for managing Widgets in a graphic view
