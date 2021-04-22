from PyQt5 import QtCore
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QDockWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PWS Calibration Suite")

        self.openMMButton = QPushButton("Open Acquisiton Software", self)
        self.runButton = QPushButton("Run Calibration", self)

        l = QVBoxLayout()
        l.addWidget(self.openMMButton)
        l.addWidget(self.runButton)
        l.addWidget(QWidget(), stretch=1)  # Push other widgets up.

        leftWidget = QDockWidget(self)
        leftWidget.setTitleBarWidget(QWidget())  # Get rid of the title bar
        leftWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        _ = QWidget(self)
        _.setLayout(l)
        leftWidget.setWidget(_)

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, leftWidget)

        self.resize(1024, 768)

