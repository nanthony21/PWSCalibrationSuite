import subprocess
import typing

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QDockWidget, QMessageBox
import os
import pwspy.utility.acquisition

from pws_calibration_suite._comparison.ITOMeasurement import ITOMeasurement
from pws_calibration_suite._comparison.analyzer import Analyzer
from pws_calibration_suite._comparison.loaders import AbstractMeasurementLoader
from pws_calibration_suite._javaGate import MMGate
import pathlib as pl

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
        self._openMMButton.released.connect(self._openMicroManager)

        self._connectButton = QPushButton("Connect", self)
        self._connectButton.released.connect(self._connectMM)

        self._runButton = QPushButton("Run Calibration", self)
        self._runButton.released.connect(lambda: QMessageBox.information(self, "NotImplemented", "Not Implemented!"))

        l = QVBoxLayout()
        l.addWidget(self._openMMButton)
        l.addWidget(self._connectButton)
        l.addWidget(self._runButton)
        l.addWidget(QWidget(), stretch=1)  # Push other widgets up.

        self.setLayout(l)

    def _openMicroManager(self):
        mmPath = r'C:\Program Files\PWSMicroManager'
        self._mmGate.openMM(mmPath)

    def _connectMM(self):
        if self._connectButton.text() == 'Connect':
            try:
                self._mmGate.connect()
            except TimeoutError as e:
                QMessageBox.warning(self, "Connection Failed", str(e))
                return
            self._connectButton.setAutoFillBackground(True)
            self._connectButton.setText("Disconnect")
        else:
            self.acquire(pl.Path.home() / 'testingAcquisition')

    def acquire(self, path: os.PathLike):
        sequence = self._mmGate.pws.loadSequence("")
        sequence.Root.setPath(path)
        self._mmGate.pws.acquireSequence(sequence)
        seq, acqs = pwspy.utility.acquisition.loadDirectory(str(path))
        ito, reflectance, glass, scatter = acqs

        loader = Loader()
        Analyzer(loader, blurSigma=7)
        # im = self._mmGate.mm.live().snapImage(True)[0]
        # buf = im.getPixelBuffer()

class Loader(AbstractMeasurementLoader):

    def __init__(self):
        pass

    @property
    def template(self) -> ITOMeasurement:
        pass

    @property
    def measurements(self) -> typing.Sequence[ITOMeasurement]:

        pass

