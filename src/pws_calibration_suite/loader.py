import os
import typing

import pwspy

from pws_calibration_suite.comparison import ITOMeasurement, AbstractMeasurementLoader
import pwspy.analysis.pws as pwsAnalysis
import pwspy.dataTypes as pwsdt
import pathlib as pl
from pwspy.utility.acquisition import loadDirectory

#TODO, copied not changed.
class DefaultLoader(AbstractMeasurementLoader):
    """
    An ITO calibration loader for the automated calibration acquisition.

    """
    analysisSettings = pwsAnalysis.PWSAnalysisSettings.loadDefaultSettings("Recommended")
    templateDir = pl.Path.home() / 'PwspyApps' / 'PWSCalibrationSuite' / 'template'

    def __init__(self, rootDir: os.PathLike, readOnly: bool = False):
        """

        Args:
            rootDir:
            readOnly: If true then an exception will be thrown if the calibration files don't already exist. Otherwise new calibration files be begin being created.
        """
        self._measurements = self.generateITOMeasurements(rootDir, readOnly)
        self._template = ITOMeasurement(self.templateDir,
                                  pwsdt.AcqDir(self.templateDir / 'Cell1'),
                                  pwsdt.AcqDir(self.templateDir / 'Cell3'),
                                  self.analysisSettings,
                                  "ITO",
                                  readOnly=False)

    @classmethod
    def generateITOMeasurements(cls, rootDir: os.PathLike, readOnly: bool):
        seq, acqs = loadDirectory(rootDir)
        acqs = [acq.acquisition for acq in acqs]
        itoAcq, refAcq, glassAcq, scatterAcq = acqs

        name = f"ITO"
        homeDir = os.path.join(rootDir, "calibrationResults", name)
        measurement = ITOMeasurement(homeDir, itoAcq, refAcq, cls.analysisSettings, name, readOnly=readOnly)
        return [measurement]

    @property
    def template(self) -> ITOMeasurement:
        return self._template

    @property
    def measurements(self) -> typing.Tuple[ITOMeasurement]:
        return tuple(self._measurements)
