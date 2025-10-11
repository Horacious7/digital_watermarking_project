# main_window.py
from PyQt5 import QtWidgets
from gui.embed_tab import EmbedTab
from gui.verify_tab import VerifyTab

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Watermarking for Historical Photos")
        self.setGeometry(100, 100, 800, 600)

        # Tab widget
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tabs
        self.embed_tab = EmbedTab()
        self.verify_tab = VerifyTab()
        self.tabs.addTab(self.embed_tab, "Embed Watermark")
        self.tabs.addTab(self.verify_tab, "Verify Watermark")
