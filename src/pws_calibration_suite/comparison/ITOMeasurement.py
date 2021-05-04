from __future__ import annotations
import logging
import os
import typing
from pwspy import dataTypes as pwsdt
from pwspy.analysis import pws as pwsAnalysis, AbstractHDFAnalysisResults
from glob import glob

from pws_calibration_suite.comparison.fileTypes import TransformedData
from pwspy.dataTypes import AnalysisManager
from pwspy.utility.misc import cached_property


class ITOMeasurement(AnalysisManager):
    """
    This class represents a single measurement of ITO thin film calibration. This consists of a raw acquisition of the ITO thin film
    as well as an acquisition of a reference image of a glass-water interface which is used for normalization.

    Args:

    """

    ANALYSIS_NAME = 'ITOCalibration'

    def __init__(self, homeDir: str, itoAcq: pwsdt.AcqDir, refAcq: pwsdt.AcqDir,
                 settings: pwsAnalysis.PWSAnalysisSettings, name: str, readOnly: bool = False):
        """

        Args:
            homeDir: The folder where the analysis and calibration files will be cached to.
            itoAcq: The PWS acquisition of the ITO thin film calibration standard.
            refAcq: The reference PWS acquisition that will be used for data normalization during PWS analysis.
            settings: The settings object that will be passed to the PWS analysis.
            name: The name to associate with this measurement.
            readOnly: If True and the home directory or initial analysis file does not yet exist an exception will be thrown.
                This is useful to prevent new analysis files from being accidently created just due to a programming
                error or misnaming of a file path.
        """
        super().__init__(homeDir)
        self.filePath = os.path.abspath(homeDir)
        self.name = name
        self._itoAcq = itoAcq
        self._refAcq = refAcq

        if not os.path.exists(homeDir):
            if readOnly:
                raise Exception("Home directory for `Read-Only` ITOMeasurement object does not exist.")
            os.makedirs(homeDir)

        logger = logging.getLogger(__name__)
        if not self._hasAnalysis():
            if readOnly:
                raise Exception("Analysis file for `Read-Only` ITOMeasurement object does not exist.")
            logger.debug(f"Generating analysis for {self.name}")
            results = self._generateAnalysis(settings)
        else:
            logger.debug(f"Loading cached analysis for {self.name}")
            results = self.analysisResults
            assert results.settings == settings  # Make sure the same settings were used for the previously stored analysis results.
            assert results.referenceIdTag == self._refAcq.idTag  # Make sure the same reference was used in the previously stored analysis results

    @staticmethod
    def getAnalysisResultsClass() -> typing.Type[AbstractHDFAnalysisResults]:
        return pwsAnalysis.PWSAnalysisResults

    def _generateAnalysis(self, settings: pwsAnalysis.PWSAnalysisSettings) -> pwsAnalysis.PWSAnalysisResults:

        ref = self._refAcq.pws.toDataClass()
        ref.correctCameraEffects()
        analysis = pwsAnalysis.PWSAnalysis(settings, None, ref)
        im = self._itoAcq.pws.toDataClass()
        im.correctCameraEffects()
        results, warnings = analysis.run(im)
        self.saveAnalysis(results, self.ANALYSIS_NAME)
        return results

    def _hasAnalysis(self) -> bool:
        return self.ANALYSIS_NAME in self.getAnalyses()

    @property
    def analysisResults(self) -> pwsAnalysis.PWSAnalysisResults:
        return self.loadAnalysis(self.ANALYSIS_NAME)

    @cached_property
    def idTag(self) -> str:
        return self._itoAcq.pws.idTag.replace(':', '_') + '__' + self._refAcq.idTag.replace(':', '_') # We want this to be able to be used as a file name so sanitize the characters

    def saveTransformedData(self, result: TransformedData, overwrite: bool = False):
        if (result.templateIdTag in self.listTransformedData()) and (not overwrite):
            raise FileExistsError(f"A calibration result named {result.templateIdTag} already exists.")
        result.toHDF(self.filePath, result.templateIdTag, overwrite=overwrite)

    def loadTransformedData(self, templateIdTag: str) -> TransformedData:
        try:
            return TransformedData.load(self.filePath, templateIdTag)
        except OSError:
            raise OSError(f"No TransformedData file found for template: {templateIdTag} for measurement: {self.name}")

    def listTransformedData(self) -> typing.Tuple[str]:
        return tuple([TransformedData.fileName2Name(f) for f in glob(os.path.join(self.filePath, f'*{TransformedData.FileSuffix}'))])
