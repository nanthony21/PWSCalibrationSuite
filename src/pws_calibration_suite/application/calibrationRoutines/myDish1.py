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
from pws_calibration_suite.loader import DefaultLoader
import shutil
import time
import logging

from pws_calibration_suite.scoring import generateFeatures

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
        return "My Dish 1"

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
            from pws_calibration_suite import calibrationSequenceFile
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
