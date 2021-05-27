from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


def make_spider(fig: plt.Figure, pandasRow: pd.Series, title: str, color: str, rMax: float = None) -> plt.Axes:
    """Copied from https://python-graph-gallery.com/392-use-faceting-for-radar-chart
    Creates a Radar plot from the values in a pandas series.

    Args:
        pandasRow: A `Series` containing values for a number of different parameters.
        title: The title to display on the figure.
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

    # Initialise the spider plot
    fig.clear()
    ax = fig.add_subplot(polar=True)

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

    # Add a title
    plt.title(title, size=11, y=1.1)
    return ax


class ScoreVisualizer(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        fig = plt.figure()
        fig.patch.set_alpha(0.1)
        self._canvas = FigureCanvasQTAgg(fig)
        self._toolbar = NavigationToolbar2QT(self._canvas, self, coordinates=False)
        l = QGridLayout()
        l.addWidget(self._canvas, 0, 0)
        l.addWidget(self._toolbar, 1, 0)
        self.setLayout(l)

    def setData(self, data: pd.Series):
        row = data.iloc[0]  # We are assuming there is only one measurement (row) in the dataframe.
        ax = make_spider(self._canvas.figure, row, "Calibration Result", 'blue', None)
        # newWidg = FigureCanvasQT(fig)
        # if self._canvas is not None:
        #     oldWidg = self._canvas
        #     self.layout().replaceWidget(oldWidg, newWidg)
        # else:
        #     self.layout().addWidget(newWidg, 0, 0)
        # self._canvas = newWidg
