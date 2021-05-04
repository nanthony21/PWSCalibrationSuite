import random

from pws_calibration_suite.comparison.analyzer import Analyzer
from pws_calibration_suite.comparison.loaders import DateMeasurementLoader
from pws_calibration_suite.comparison.reviewer import Reviewer
import os
import logging
import sys
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication
import qdarkstyle

from pws_calibration_suite._javaGate import MMGate
from pws_calibration_suite._ui import MainWindow


def configureLogger():
    logger = logging.getLogger("pwspy")  # We get the root logger so that all loggers in pwspy will be handled.
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


class App(QApplication):
    def __init__(self):
        super().__init__([])
        style = random.choice([qdarkstyle.dark.palette.DarkPalette, qdarkstyle.light.palette.LightPalette])
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5', palette=style))
        self._mmGate = MMGate()
        try:
            self._mmGate.connect(timeout=.05)  # Try connecting immediately in case an instanse is already running.
        except:
            pass
        self._window = MainWindow(self._mmGate)
        self._window.show()
        self.aboutToQuit.connect(self.close)

    def close(self):
        self._mmGate.close()

def main():
    plt.ion()

    directory = r'\\BackmanLabNAS\home\Year3\ITOPositionStability\AppTest'

    logger = configureLogger()

    app = App()
    app.exec()

    # logger.debug("Start ITO Analyzer")
    # loader = DateMeasurementLoader(directory, os.path.join(directory, '10_20_2020'))
    # anlzr = Analyzer(loader, useCached=True)
    # rvwr = Reviewer(loader)


    a = 1  # Debug Breakpoint


if __name__ == '__main__':
    main()
