import subprocess

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QDockWidget, QMessageBox
import os

from pws_calibration_suite._javaGate import MMGate


class MainWindow(QMainWindow):
    def __init__(self, mmGate: MMGate):
        super().__init__()
        self.setWindowTitle("PWS Calibration Suite")
        self._mmGate = mmGate


        leftWidget = QDockWidget(parent=self)
        leftWidget.setTitleBarWidget(QWidget())  # Get rid of the title bar
        leftWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        leftWidget.setWidget(AcquireWidget(mmGate, parent=leftWidget))

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, leftWidget)

        self.resize(1024, 768)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self._mmGate.close()
        print("Closing!")
        super().closeEvent(a0)


class AcquireWidget(QWidget):
    def __init__(self, mmGate: MMGate, parent: QWidget = None):
        super().__init__(parent=parent)

        self._mmGate = mmGate

        self._openMMButton = QPushButton("Open Acquisiton Software", self)
        self._runButton = QPushButton("Run Calibration", self)

        self._openMMButton.released.connect(self.openMicroManager)

        self._runButton.released.connect(lambda: QMessageBox.information(self, "NotImplemented", "Not Implemented!"))

        l = QVBoxLayout()
        l.addWidget(self._openMMButton)
        l.addWidget(self._runButton)
        l.addWidget(QWidget(), stretch=1)  # Push other widgets up.

        self.setLayout(l)

    def openMicroManager(self):
        mmPath = r'C:\Program Files\PWSMicroManager'
        self._mmGate.openMM(mmPath)
        try:
            self._mmGate.connect()
        except TimeoutError as e:
            QMessageBox.warning(self, "Connection Failed", str(e))
            return
        self._openMMButton.setBackgroundRole(QColor().green())
        self._openMMButton.setText("Close Acquisition")

