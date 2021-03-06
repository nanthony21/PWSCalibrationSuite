from PWSCalibrationSuite._utility import CubeSplitter
from PWSCalibrationSuite.analyzer import Analyzer
import os
import logging
import sys
import matplotlib.pyplot as plt

from PWSCalibrationSuite.loaders import DateMeasurementLoader
from PWSCalibrationSuite.reviewer import Reviewer
from mpl_qt_viz.visualizers import PlotNd
import pandas as pd
import numpy as np


def configureLogger():
    logger = logging.getLogger("pwspy")  # We get the root logger so that all loggers in pwspy will be handled.
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


def main():
    plt.ion()

    directory = r'\\BackmanLabNAS\home\Year3\ITOPositionStability\AppTest'

    logger = configureLogger()

    logger.debug("Start ITO Analyzer")
    loader = DateMeasurementLoader(directory, os.path.join(directory, '10_20_2020'))
    anlzr = Analyzer(loader, useCached=True)
    rvwr = Reviewer(loader)


    a = 1  # Debug Breakpoint


if __name__ == '__main__':
    main()
