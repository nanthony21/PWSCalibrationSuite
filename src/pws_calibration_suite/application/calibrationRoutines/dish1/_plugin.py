from __future__ import annotations
import joblib
from mpl_qt_viz.visualizers import DockablePlotWindow
from sklearn.preprocessing import StandardScaler

from pws_calibration_suite import scalerPath
from pws_calibration_suite.application._ui.scorevisualizer import RadarPlot
from pws_calibration_suite.application.calibrationRoutines import RoutinePlugin
import typing as t_
import pathlib as pl

from pws_calibration_suite.comparison.analyzer import Analyzer
from pws_calibration_suite.application.calibrationRoutines.dish1._loader import DefaultLoader
import shutil
import time
import logging

import pandas as pd
import numpy as np

if t_.TYPE_CHECKING:
    from pws_calibration_suite.application.controller import Controller


class MyRoutine(RoutinePlugin):
    def __init__(self, controller: Controller, visualizer: DockablePlotWindow):
        self._controller = controller
        self._visualizer = visualizer

    @classmethod
    def instantiate(cls, controller: Controller, visualizer: DockablePlotWindow):
        return MyRoutine(controller, visualizer)

    def getName(self):
        return "Plate1: ITO"

    def run(self):
        path = pl.Path.home() / 'testingAcquisition'
        if not path.exists():
            path.mkdir()
        loader = self._acquire(path, simulated=True)
        an = Analyzer(loader, blurSigma=3)
        # Convert the score object to an dataframe of values
        df = generateFeatures(an.output)
        scaler: StandardScaler = joblib.load(scalerPath)
        df[:] = scaler.transform(df) / 100 + 1

        row = df.iloc[0]  # We are assuming there is only one measurement (row) in the dataframe.
        _ = RadarPlot(self._visualizer, row)
        self._visualizer.addWidget(_, "Calibration Results")

        return an.output

    def _acquire(self, path: pl.Path, simulated: bool = False) -> DefaultLoader:
        """
        Command the acquisition software to acquire a sequence acquisition.

        Args:
            path: The file path to save the data to.
            simulated: If `True` then existing data is loaded without actually having the acquisition software run anything.

        Returns:
            A `Loader` object to provide access to the acquired data.
        """
        logger = logging.getLogger(__name__)
        logger.debug("Starting acquisition.")
        if not simulated:
            from . import calibrationSequenceFile
            sequencerapi = self._controller.getGate().pws.sequencer()
            sequencerapi.loadSequence(str(calibrationSequenceFile))
            if path.exists():
                shutil.rmtree(path)
            path.mkdir()
            sequencerapi.setSavePath(str(path))
            sequencerapi.runSequence()
            while sequencerapi.isSequenceRunning():
                time.sleep(.5)
        logger.debug("Loading.")
        loader = DefaultLoader(path)
        logger.debug("Done loading.")
        return loader

def generateFeatures(rawDf: pd.DataFrame):
    # Split the `CombinedScore` object into numerical columns that will be used as inputs
    funcDict = {
        'latXCorr': lambda row: row.score.latxcorr.score,
        'latXCorr_cdr': lambda row: np.sqrt((row.score.latxcorr.cdrY**2 + row.score.latxcorr.cdrX**2)/2),  # RMS of cdrx and cdry. Looking at data by eye this didn't look that useful, I'm inclined to get rid of it.
        'latXCorr_cdr_eccent': lambda row: row.score.latxcorr.cdrY/row.score.latxcorr.cdrX,  # TODO this is not how eccentricity is measured and we will need to measure the major and minor axes of the the CDR not just X and Y
        'axXCorr': lambda row: row.score.axxcorr.score,
        'axXCorr_cdr': lambda row: row.score.axxcorr.cdr,
        'axXCorr_shift': lambda row: row.score.axxcorr.shift,
        'nrmse': lambda row: row.score.nrmse.score,
        'ssim': lambda row:  row.score.ssim.score,
        'reflectance': lambda row: row.score.reflectance.reflectanceRatio
    }
    df = pd.DataFrame()
    for k, v in funcDict.items():
        df[k] = rawDf.apply(v, axis=1)
    return df