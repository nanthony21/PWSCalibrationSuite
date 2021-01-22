from PWSCalibrationSuite.ITOMeasurement import ITOMeasurement
from PWSCalibrationSuite.loaders import AbstractMeasurementLoader
import typing
import pwspy.analysis.pws as pwsAnalysis
import os
import pwspy.dataTypes as pwsdt


class Loader(AbstractMeasurementLoader):
    """
    An ITO calibration loader for this experiment. The reference for each ITO acquisiton is Cell3 from the same experiemental condition

    """
    analysisSettings = pwsAnalysis.PWSAnalysisSettings.loadDefaultSettings("Recommended")

    def __init__(self, rootDir: str, measurementSetName: str, readOnly: bool = False):
        """

        Args:
            rootDir:
            measurementSetName:
            readOnly: If true then an exception will be thrown if the calibration files don't already exist. Otherwise new calibration files be begin being created.
        """
        meas = self.generateITOMeasurements(rootDir, measurementSetName, readOnly)
        template = [m for m in meas if m.name == 'centered_0_52'][0]
        self._template = template
        self._measurements = meas

    @classmethod
    def generateITOMeasurements(cls, rootDir: str, measurementSetName: str, readOnly: bool):
        measurements = []
        for expType in ['centered', 'fieldstop', 'translation']:
            for condition in os.listdir(os.path.join(rootDir, expType)):
                if os.path.isdir(os.path.join(rootDir, expType, condition)):
                    itoAcq = pwsdt.AcqDir(os.path.join(rootDir, expType, condition, 'ito', 'Cell1'))
                    refAcq = pwsdt.AcqDir(os.path.join(rootDir, expType, condition, 'cells', "Cell3"))
                    name = f"{expType}_{condition}"
                    homeDir = os.path.join(rootDir, "calibrationResults", measurementSetName, name)
                    measurements.append(ITOMeasurement(homeDir, itoAcq, refAcq, cls.analysisSettings, name, readOnly=readOnly))
        return measurements

    @property
    def template(self) -> ITOMeasurement:
        return self._template

    @property
    def measurements(self) -> typing.Tuple[ITOMeasurement]:
        return tuple(self._measurements)
