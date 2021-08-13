from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QGridLayout, QFormLayout, QDoubleSpinBox, QSlider
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


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
        self.slider = QSlider(QtCore.Qt.Horizontal, self)
        self.slider.sliderReleased.connect(lambda: self.slider.setValue(0))
        self.slider.setMinimum(-10)
        self.slider.setMaximum(10)

        self.sliderVal = self._ax.get_ylim()[1]
        self.radiusBox = QDoubleSpinBox(self)
        self.radiusBox.setValue(self.sliderVal)
        self.radiusBox.valueChanged.connect(self._valChanged)

        l = QFormLayout()
        l.addRow(self.slider)
        l.addRow("Radius: ", self.radiusBox)
        self.setLayout(l)

    def _valChanged(self, value: float):
        self._ax.set_ylim(0, value)
        self._canv.draw_idle()

    def _evalTimer(self):
        value = self.slider.value()
        # Convert value
        neg = -1 if value < 0 else 1
        value = neg * (2**(abs(value)/10) - 1)  # TODO exponent
        val = self._ax.get_ylim()[1] + value
        self.radiusBox.setValue(val)
