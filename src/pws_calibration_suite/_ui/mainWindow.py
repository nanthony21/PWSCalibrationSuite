import logging

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QDockWidget, QMessageBox
import os
import pwspy.utility.acquisition
import time
from pws_calibration_suite.comparison.analyzer import Analyzer
from pws_calibration_suite._javaGate import MMGate
import pathlib as pl

from pws_calibration_suite.loader import Loader


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

        connectStr = "Disconnect" if self._mmGate.isConnected() else "Connect"
        self._connectButton = QPushButton(connectStr, self)
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
        logger = logging.getLogger(__name__)
        if self._connectButton.text() == 'Connect':
            try:
                self._mmGate.connect()
            except TimeoutError as e:
                QMessageBox.warning(self, "Connection Timed Out", str(e))
                logger.exception(e)
                return
            except Exception as e:
                QMessageBox.warning(self, "Connection Timed Out", str(e))
                logger.exception(e)
                return
            self._connectButton.setAutoFillBackground(True)
            self._connectButton.setText("Disconnect")
        else:
            path = pl.Path.home() / 'testingAcquisition'
            if not path.exists():
                path.mkdir()
            self.acquire(path)

    def acquire(self, path: os.PathLike):
        from pws_calibration_suite import calibrationSequenceFile
        sequencerapi = self._mmGate.pws.sequencer()
        sequencerapi.loadSequence(str(calibrationSequenceFile))
        sequencerapi.setSavePath(str(path))
        sequencerapi.runSequence()
        time.sleep(1)
        while (sequencerapi.isSequenceRunning()):
            time.sleep(1)
            print('Waiting')
        seq, acqs = pwspy.utility.acquisition.loadDirectory(str(path))
        ito, reflectance, glass, scatter = acqs

        loader = Loader()
        Analyzer(loader, blurSigma=7)
        # im = self._mmGate.mm.live().snapImage(True)[0]
        # buf = im.getPixelBuffer()


