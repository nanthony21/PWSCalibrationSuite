import logging

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QDialog, QFormLayout, QSpinBox, QDoubleSpinBox, QSlider
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from mpl_qt_viz.visualizers import DockablePlotWindow
from pip._internal.utils import logging
from qtpy import QtCore


# def make_spider(ax: plt.Axes, pandasRow: pd.Series, color: str, rMax: float = None) -> plt.Axes:
#     """Copied from https://python-graph-gallery.com/392-use-faceting-for-radar-chart
#     Creates a Radar plot from the values in a pandas series.
#
#     Args:
#         pandasRow: A `Series` containing values for a number of different parameters.
#         color: The matplotlib `color` to use.
#         rMax: The maximum radius of the radar plot. If left as `None` this will be set to the maximum value of
#             `pandasRow`.
#     """
#     # number of variable
#     categories = list(pandasRow.index)
#     N = len(categories)
#
#     # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
#     angles = [n / float(N) * 2 * np.pi for n in range(N)]
#     angles += angles[:1]
#
#     # If you want the first axis to be on top:
#     ax.set_theta_offset(np.pi / 2)
#     ax.set_theta_direction(-1)
#
#     # Draw one axe per variable + add labels labels yet
#     plt.xticks(angles[:-1], categories, color='grey', size=8)
#
#     # Draw ylabels
#     ax.set_rlabel_position(0)
#     rMax = max(pandasRow) if rMax is None else rMax
#     plt.ylim(0, rMax)
#
#     # Ind1
#     values = pandasRow.values.flatten().tolist()
#     values += values[:1]
#     ax.plot(angles, values, color=color, linewidth=2, linestyle='solid')
#     ax.fill(angles, values, color=color, alpha=0.4)

    # return ax


class ScoreVisualizer(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._dockWidg = DockablePlotWindow()
        l = QGridLayout()
        l.addWidget(self._dockWidg, 0, 0)
        self.setLayout(l)

    def addSubplot(self, title: str, polar: bool = False):
        fig, ax = self._dockWidg.subplots(title, subplot_kw={'polar': polar})
        return fig, ax

    def setData(self, data: pd.Series):
        row = data.iloc[0]  # We are assuming there is only one measurement (row) in the dataframe.
        # fig, ax = self.addSubplot("Calibration Result", polar=True)
        # ax = make_spider(ax, row, 'blue', None)
        _ = RadarPlot(self, row)
        self._dockWidg.addWidget(_, "Calibration Results")


class RadarPlot(QWidget):
    """
    Creates a Radar plot from the values in a pandas series.

    Args:
        data: A `Series` containing values for a number of different parameters.
    """
    def __init__(self, parent: QWidget, data: pd.Series):
        super().__init__(parent=parent)
        interactive = False
        if plt.isinteractive():
            interactive = True
            plt.ioff()
        fig, ax = plt.subplots(subplot_kw={'polar': True})
        self._ax = ax
        if interactive:
            plt.ion()  # Set back to interactive if it originally was.
        fig.suptitle("Calibration Results")
        self._canv = FigureCanvasQTAgg(figure=fig)
        self._canv.setFocusPolicy(QtCore.Qt.ClickFocus)
        self._canv.setFocus()
        self._bar = NavigationToolbar2QT(self._canv, self)
        self._optionsPane = OptionDialog(self._ax, self._canv, self)
        # self._optionsButton = QPushButton("Options", self)
        # self._optionsButton.released.connect(self._optionsDlg)
        l = QGridLayout()
        l.addWidget(self._canv, 0, 0)
        l.addWidget(self._bar, 1, 0)
        l.addWidget(self._optionsPane, 0, 1)
        # l.addWidget(self._optionsButton, 1, 1)
        self.setLayout(l)

        self.setData(ax, data)

    @staticmethod
    def setData(ax: plt.Axes, data: pd.Series):
        assert isinstance(data, pd.Series), f"`data` must be a Pandas Series, not: {type(data)}"
        # number of variable
        categories = list(data.index)
        N = len(categories)

        # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]

        # If you want the first axis to be on top:
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # Draw one axe per variable + add labels labels yet
        plt.xticks(angles[:-1], categories, color='grey', size=8)

        # Draw ylabels
        ax.set_rlabel_position(0)
        rMax = max(data)  # if rMax is None else rMax
        ax.set_ylim(0, rMax)

        # Ind1
        values = data.values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, color='blue', linewidth=2, linestyle='solid')
        ax.fill(angles, values, color='blue', alpha=0.4)

    def _optionsDlg(self):
        dlg = OptionDialog(self._ax, self._canv, self)
        dlg.exec()


class OptionDialog(QWidget):
    def __init__(self, ax: plt.Axes, canv: plt.FigureCanvasBase, parent: QWidget):
        super().__init__(parent)#, flags=QtCore.Qt.FramelessWindowHint)
        self._ax = ax
        self._canv = canv
        self._timer = QTimer(self)
        self._timer.setInterval(10)
        self._timer.setSingleShot(False)
        self._timer.timeout.connect(self._evalTimer)
        self._timer.start()
        self.slider = QSlider(QtCore.Qt.Vertical, self)
        self.slider.sliderReleased.connect(lambda: self.slider.setValue(0))
        self.slider.valueChanged.connect(self._sliderValChanged)
        self.slider.setMinimum(-10)
        self.slider.setMaximum(10)

        self.sliderVal = self._ax.get_ylim()[1]
        self.radiusBox = QDoubleSpinBox(self)
        self.radiusBox.setValue(self.sliderVal)
        self.radiusBox.valueChanged.connect(self._valChanged)

        # okButton = QPushButton("OK", self)
        # okButton.released.connect(self.accept)

        l = QFormLayout()
        l.addRow(self.slider)
        l.addRow("Radius: ", self.radiusBox)
        # l.addRow(okButton)
        self.setLayout(l)

    def _valChanged(self, value: float):
        self._ax.set_ylim(0, value)
        self._canv.draw_idle()

    def _sliderValChanged(self, value: float):
        pass
        # self.sliderVal = val
        # self.radiusBox.setValue(val)

    def _evalTimer(self):
        value = self.slider.value()
        # Convert value
        neg = -1 if value < 0 else 1
        logging.getLogger(__name__).debug(f"{value}")
        value = neg * (2**(abs(value)/10) - 1)  # TODO exponent
        logging.getLogger(__name__).debug(f"b{value}")
        val = self._ax.get_ylim()[1] + value
        self.radiusBox.setValue(val)
        # self._ax.set_ylim(0, val)
        # self._canv.draw_idle()
