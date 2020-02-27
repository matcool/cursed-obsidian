"""
this sucks i will probably just use imgui (99999x easier)
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import curseforge
import threading
from typing import Tuple

class SearchAddonsThread(QThread):
    done_signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.query = None

    def run(self):
        addons = curseforge.Addon.search_addon(self.query)
        self.done_signal.emit(addons)

class ModWidget(QWidget):
    def __init__(self, title, description, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hlayout = QHBoxLayout(self)

        img = QLabel()
        img.setAlignment(Qt.AlignLeft)
        img.setPixmap(QPixmap('farlands.png').scaled(100, 100))
        hlayout.addWidget(img)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignLeft)

        title = QLabel(title)
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("QLabel {background-color: red;}")
        layout.addWidget(title)

        # description = QLabel(description)
        # description.setAlignment(Qt.AlignLeft)
        # layout.addWidget(description)

        hlayout.addLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle('Search for a mod')

        self.layout = QVBoxLayout()

        search_layout = QHBoxLayout()

        self.mod_input = QLineEdit('farlands')
        self.mod_input.setAlignment(Qt.AlignLeft)
        search_layout.addWidget(self.mod_input)

        search_btn = QPushButton()
        search_btn.clicked.connect(self.search)
        search_layout.addWidget(search_btn)

        self.search_thread = SearchAddonsThread()
        self.search_thread.done_signal.connect(self.search_done)

        self.layout.addLayout(search_layout)

        widget = QWidget()
        widget.setLayout(self.layout)

        self.setCentralWidget(widget)

    def search(self):
        if self.search_thread.isRunning(): return
        self.search_thread.query = self.mod_input.text()
        self.search_thread.start()

    def search_done(self, addons):
        for add in addons:
            mod = ModWidget(add.name, add.summary)
            self.layout.addWidget(mod)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

exit(app.exec_())