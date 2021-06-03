import logging
import pandas as pd
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QDockWidget, QMessageBox
from pws_calibration_suite._ui.controller import Controller
from pws_calibration_suite._javaGate import MMGate
import pathlib as pl
from pws_calibration_suite import targetIconPath, scalerPath
from pws_calibration_suite._ui.scorevisualizer import ScoreVisualizer
from pws_calibration_suite.comparison.analyzer import Analyzer
from pws_calibration_suite.scoring import generateFeatures
import joblib
from sklearn.preprocessing import StandardScaler


class MainWindow(QMainWindow):
    def __init__(self, mmGate: MMGate):
        super().__init__()
        self.setWindowTitle("PWS Calibration Suite")
        self.setWindowIcon(QIcon(str(targetIconPath)))

        self._controller = Controller(mmGate)
        self._visualizerWidg = ScoreVisualizer(self)

        leftWidget = QDockWidget(parent=self)
        self._acquireWidg = AcquireWidget(self._controller, self._visualizerWidg, parent=leftWidget)

        leftWidget.setTitleBarWidget(QWidget())  # Get rid of the title bar
        leftWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        leftWidget.setWidget(self._acquireWidg)

        self.setCentralWidget(self._visualizerWidg)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, leftWidget)

        self.resize(1024, 768)

        self._acquireWidg.newDataAcquired.connect(self._visualizerWidg.setData)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self._controller.getGate().close()
        print("Closing!")
        super().closeEvent(a0)


class AcquireWidget(QWidget):
    newDataAcquired = pyqtSignal(pd.DataFrame)

    def __init__(self, controller: Controller, visualizer: ScoreVisualizer, parent: QWidget = None):
        super().__init__(parent=parent)
        self._controller = controller
        self._visualizer = visualizer

        self._openMMButton = QPushButton("Open Acquisiton Software", self)
        self._openMMButton.released.connect(self._openMicroManager)

        connectStr = "Disconnect" if self._controller.getGate().isConnected() else "Connect"
        self._connectButton = QPushButton(connectStr, self)
        self._connectButton.released.connect(self._connectMM)

        self._runButton = QPushButton("Run Calibration", self)
        self._runButton.released.connect(self.acquire)  # lambda: QMessageBox.information(self, "NotImplemented", "Not Implemented!"))

        self._snapButton = QPushButton("Snap", self)
        self._snapButton.released.connect(self._snap)

        l = QVBoxLayout()
        l.addWidget(self._openMMButton)
        l.addWidget(self._connectButton)
        l.addWidget(self._runButton)
        l.addWidget(self._snapButton)
        l.addWidget(QWidget(), stretch=1)  # Push other widgets up.

        self.setLayout(l)

    def _openMicroManager(self):
        mmPath = r'C:\Program Files\PWSMicroManager'
        self._controller.getGate().openMM(mmPath)

    def _connectMM(self):
        logger = logging.getLogger(__name__)
        if self._connectButton.text() == 'Connect':
            try:
                self._controller.getGate().connect()
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
            pass

    def _snap(self):
        image = self._controller.snap()
        fig, ax = self._visualizer.addSubplot("Snap")
        ax.imshow(image.arr, cmap='gray')

    def acquire(self) -> pd.DataFrame:
        path = pl.Path.home() / 'testingAcquisition'
        if not path.exists():
            path.mkdir()
        loader = self._controller.acquire(path, simulated=True)
        an = Analyzer(loader, blurSigma=3)
        # Convert the score object to an dataframe of values
        df = generateFeatures(an.output)
        scaler: StandardScaler = joblib.load(scalerPath)
        df[:] = scaler.transform(df) / 100 + 1
        self.newDataAcquired.emit(df)
        return an.output


