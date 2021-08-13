import random

import qdarkstyle
from PyQt5.QtWidgets import QApplication

from pws_calibration_suite.application._javaGate import MMGate
from pws_calibration_suite.application._ui import MainWindow


class App(QApplication):
    def __init__(self):
        super().__init__([])
        # style = random.choice([qdarkstyle.dark.palette.DarkPalette, qdarkstyle.light.palette.LightPalette])
        # self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5', palette=style))
        self._mmGate = MMGate()
        try:
            self._mmGate.connect(timeout=.05)  # Try connecting immediately in case an instance is already running.
        except:
            pass
        self._window = MainWindow(self._mmGate)
        self._window.show()
        self.aboutToQuit.connect(self.close)

    def close(self):
        self._mmGate.close()
