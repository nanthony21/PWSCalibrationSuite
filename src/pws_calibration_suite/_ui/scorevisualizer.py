from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mpl_qt_viz.visualizers import DockablePlotWindow


def make_spider(ax: plt.Axes, pandasRow: pd.Series, color: str, rMax: float = None) -> plt.Axes:
    """Copied from https://python-graph-gallery.com/392-use-faceting-for-radar-chart
    Creates a Radar plot from the values in a pandas series.

    Args:
        pandasRow: A `Series` containing values for a number of different parameters.
        color: The matplotlib `color` to use.
        rMax: The maximum radius of the radar plot. If left as `None` this will be set to the maximum value of
            `pandasRow`.
    """
    # number of variable
    categories = list(pandasRow.index)
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
    rMax = max(pandasRow) if rMax is None else rMax
    plt.ylim(0, rMax)

    # Ind1
    values = pandasRow.values.flatten().tolist()
    values += values[:1]
    ax.plot(angles, values, color=color, linewidth=2, linestyle='solid')
    ax.fill(angles, values, color=color, alpha=0.4)

    return ax


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
        fig, ax = self.addSubplot("Calibration Result", polar=True)
        ax = make_spider(ax, row, 'blue', None)
