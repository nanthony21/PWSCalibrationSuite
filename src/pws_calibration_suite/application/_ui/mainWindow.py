from __future__ import annotations
import logging
import py4j.protocol
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QDockWidget, QMessageBox, QFrame, QLabel
from mpl_qt_viz.visualizers import DockablePlotWindow

from pws_calibration_suite.application.calibrationRoutines import RoutinePluginManager
from pws_calibration_suite.application.controller import Controller
from pws_calibration_suite import targetIconPath
import typing as t_
if t_.TYPE_CHECKING:
    from pws_calibration_suite.application.javaGate._mmGate import MMGate


class MainWindow(QMainWindow):
    def __init__(self, mmGate: MMGate):
        super().__init__()
        self.setWindowTitle("PWS Calibration Suite")
        self.setWindowIcon(QIcon(str(targetIconPath)))

        self._controller = Controller(mmGate)
        self._visualizerWidg = DockablePlotWindow()

        leftWidget = QDockWidget(parent=self)
        self._acquireWidg = AcquireWidget(self._controller, self._visualizerWidg, parent=leftWidget)

        leftWidget.setTitleBarWidget(QWidget())  # Get rid of the title bar
        leftWidget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        leftWidget.setWidget(self._acquireWidg)

        self.setCentralWidget(self._visualizerWidg)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, leftWidget)

        self.resize(1024, 768)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self._controller.getGate().close()
        super().closeEvent(a0)


class AcquireWidget(QWidget):

    def __init__(self, controller: Controller, visualizer: DockablePlotWindow, parent: QWidget = None):
        super().__init__(parent=parent)
        self._controller = controller
        self._visualizer = visualizer

        self._routineManager = RoutinePluginManager(self._controller, self._visualizer, self)

        self._connectButton = QPushButton("", self)
        self._connectButton.released.connect(self._connectMM)
        self._setUIConnected(self._controller.getGate().isConnected())

        self._snapButton = QPushButton("Snap", self)
        self._snapButton.released.connect(self._snap)

        l = QVBoxLayout()
        l.addWidget(self._connectButton)
        l.addWidget(self._snapButton)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        l.addWidget(line)
        l.addWidget(QLabel("Calibration Routines"))
        for i in self._routineManager.getPlugins():
            button = QPushButton(i.getName(), self)
            button.released.connect(lambda routine=i: routine.run())
            l.addWidget(button)
        l.addWidget(QWidget(), stretch=1)  # Push other widgets up.

        self.setLayout(l)

    def _openMicroManager(self):
        self._controller.getGate().openMM()
        if self._controller.getGate().isConnected():
            self._setUIConnected(True)

    def _setUIConnected(self, connected: bool):
        if connected:
            # self._connectButton.setAutoFillBackground(True)
            self._connectButton.setEnabled(False)
            self._connectButton.setText("Connected")
        else:
            self._connectButton.setEnabled(True)
            self._connectButton.setText("Connect")

    def _isUIConnected(self) -> bool:
        return not self._connectButton.text() == 'Connect'

    def _connectMM(self):
        logger = logging.getLogger(__name__)
        if not self._isUIConnected():
            try:
                self._controller.getGate().connect(timeout=0.5)
                self._setUIConnected(True)
            except TimeoutError as e:
                result = QMessageBox.question(self, "Open Micro-Manager?",
                                     "Could not find an instance of PWS Micro-Manager. Attempt to open a new instance?")
                if result == QMessageBox.Yes:
                    self._openMicroManager()
                return
            except Exception as e:
                QMessageBox.warning(self, "Connection Error", str(e))
                logger.exception(e)
                return
        else:
            RuntimeError("Reached unallowed condition.")

    def _snap(self):
        try:
            image = self._controller.snap()
        except py4j.protocol.Py4JError as e:
            QMessageBox.warning(self, "Error", f"Snap failed with error: {str(e)}")
            return
        fig, ax = self._visualizer.subplots("Snap")
        ax.imshow(image.arr, cmap='gray')



