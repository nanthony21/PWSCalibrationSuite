# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 16:44:06 2020

@author: nick
"""
from __future__ import annotations
import typing as t_
import multiprocessing as mp
import cv2
import pandas as pd
from scipy.ndimage import binary_dilation
from pws_calibration_suite.comparison.TransformGenerator import TransformGenerator
from pwspy.utility.fileIO import processParallel

from . import ITOMeasurement
from ._scorers import *
from ._utility import CVAffineTransform
from .fileTypes import TransformedData
from .loaders import settings, AbstractMeasurementLoader
from pwspy.utility.reflection import Material

settings.referenceMaterial = Material.Air


def _blur3dDataLaterally(data: np.ndarray, sigma: float) -> np.ndarray:
    """
    Blur a 3D array along the first and second dimension.
    Args:
        data: A 3d numpy array
        sigma: The width of the gaussian kernel used for blurring. In units of pixels.

    Returns:
        The blurred data.
    """
    from scipy import ndimage
    newData = np.zeros_like(data)
    for i in range(data.shape[2]):
        newData[:, :, i] = ndimage.filters.gaussian_filter(data[:, :, i], sigma, mode='reflect')
    return newData


def _score(measurement: ITOMeasurement, scoreName: str, blurSigma: float, templateIdTag: str, templateArr: np.ndarray, lock: mp.Lock = None) -> pd.Series:
    logger = logging.getLogger(__name__)
    logger.debug(f"Scoring measurement {measurement.name}")
    tData = measurement.loadTransformedData(templateIdTag=templateIdTag)
    slc = tData.getValidDataSlice()
    templateSubArr = templateArr[slc]
    testArr = tData.transformedData[slc]
    if blurSigma is not None:
        testArr = _blur3dDataLaterally(testArr, blurSigma)
    score = CombinedScore.create(templateSubArr, testArr)
    if lock is not None:
        lock.acquire()
    try:
        tData.addScore(scoreName, score, overwrite=True)
    finally:
        if lock is not None:
            lock.release()
        return pd.Series({'measurement': measurement, 'score': score})


def parallelInit(lck: mp.Lock, templateArr: np.ndarray):
    global _lock
    _lock = lck
    global _templateArr
    _templateArr = templateArr


def parallelScoreWrapper(row, args):
    i, row = row
    mp.get_logger().warning(f"Scoring measurement {row.measurement.name}")  # We use warning since the `info` level already has a log of unwanted messages.
    _score(row.measurement, *args, templateArr=_templateArr, lock=_lock)


def createSharedArray(array: np.ndarray) -> np.ndarray:
    import ctypes
    assert array.dtype == np.float32
    sharedArr = mp.RawArray(ctypes.c_float, array.size)
    npSharedArr = np.frombuffer(sharedArr, dtype=array.dtype).reshape(array.shape)
    np.copyto(npSharedArr, array)
    return npSharedArr


class TransformedDataScorer:
    """This class uses a template measurement to analyze a series of other measurements and give them scores for how
     well they match to the template.

     Args:
        loader: A data loader object that provides access to a `template` measurement and a sequence of `measurement`
            measurements.
        scoreName: This string is used to save the score information to the "TransformedData" file. Each file can only
            have a single score for a given name.
        blurSigma: This value determines the `sigma` of the gaussian blur of the template and measurement data that occurs
            at the beginning of the scoring process. This blur helps to reduce the effects of random measurement noise
            and slight pixel-scale differences in data alignment. Too much blurring can reduce sensitivity of the scorers.
        parallel: If `True` the measurements will be scored in parallel on multiple cores. Will use much more RAM but
            will be faster in most situations when many measurements need to be scored.
     """

    def __init__(self, loader: AbstractMeasurementLoader, scoreName: str, blurSigma: t_.Optional[float] = 2,
                 parallel: bool = False):
        # Scoring the bulk arrays
        templateArr: np.ndarray = (loader.template.analysisResults.reflectance + loader.template.analysisResults.meanReflectance[:, :, None]).data
        if blurSigma is not None:
            templateArr = _blur3dDataLaterally(templateArr, blurSigma)
        df = pd.DataFrame({"measurement": loader.measurements})

        if parallel:
            mplogger = mp.get_logger()
            mplogger.setLevel(logging.WARNING)
            lock = mp.Lock()
            sharedArr = createSharedArray(templateArr)
            out = processParallel(df, parallelScoreWrapper, procArgs=(scoreName, blurSigma, loader.template.idTag),
                                  initializer=parallelInit, initArgs=(lock, sharedArr), numProcesses=4)
        else:
            procArgs = (scoreName, blurSigma, loader.template.idTag, templateArr)
            out = df.apply(lambda row: _score(row.measurement, *procArgs), axis=1)
        self.output = pd.DataFrame(out)


class TransformedDataSaver:
    """
    This class uses a template measurement to identify the affine transformation between the template data and the test
    data. The test data is aligned to the template and saved to an HDF file.

    Args:
        loader: A data loader object that provides access to a `template` measurement and a sequence of `measurement`
            measurements.
        useCached: If `True` then load cached information about the affine transforms if available. Saves processing time.
        debugMode: Runs the data transform generator in debug mode. Plots will be opened that display the results of
            the transform generation.
        method: Selects which method the transform generator should use. All possible options are stored in the
            `TransformGenerator.Method` enum.

    """
    def __init__(self, loader: AbstractMeasurementLoader, useCached: bool = True, debugMode: bool = False, method: TransformGenerator.Method = TransformGenerator.Method.XCORR):
        self._loader = loader
        logger = logging.getLogger(__name__)

        resultPairs = []
        if useCached:
            needsProcessing = []
            for m in self._loader.measurements:
                if self._loader.template.idTag in m.listTransformedData():
                    logger.debug(f"Loading cached results for {m.name}")
                    result = m.loadTransformedData(self._loader.template.idTag)
                    resultPairs.append((m, result))
                else:  # No cached result was found. Add the measurement to the `needProcessing` list
                    needsProcessing.append(m)
        else:
            needsProcessing = self._loader.measurements

        self._matcher = TransformGenerator(loader.template.analysisResults, debugMode=debugMode, method=method)
        transforms = self._matcher.match([i.analysisResults for i in needsProcessing])

        transformedData = []
        for transform, measurement in zip(transforms, needsProcessing):
            if transform is None:
                logger.debug(f"Skipping transformation of {measurement.name}")
            else:
                transformedData.append(self._transformData(measurement, transform))

        for measurement, tData in zip(needsProcessing, transformedData):
            measurement.saveTransformedData(tData, overwrite=True)

    def _transformData(self, measurement: ITOMeasurement, transform: np.ndarray) -> TransformedData:
        """

        Args:
            measurement: A single `Measurement` of the calibration standard
            transform: The 2x3 affine transformation mapping the raw data to the template data.

        Returns:
            A transformeddata object
        """
        # transform = self._coerceAffineTransform(transform)
        reflectance = self._applyTransform(transform, measurement)
        return TransformedData.create(templateIdTag=self._loader.template.idTag,
                                      affineTransform=transform,
                                      transformedData=reflectance,
                                      methodName=self._matcher.getMethodName())

    @staticmethod
    def _coerceAffineTransform(transform: np.ndarray):
        """This is not currently used but it used to be, keeping it around just in case. Given a 2x3 affine transform the transform will have its scale set
        to 1 and its rotation set to 0, leaving only translation."""
        transform = CVAffineTransform.fromPartialMatrix(transform)
        assert abs(transform.scale[0]-1) < .005, f"The estimated transform includes a scaling factor of {abs(transform.scale[0]-1)*100} percent!"
        assert np.abs(np.rad2deg(transform.rotation)) < .2, f"The estimated transform includes a rotation of {np.rad2deg(transform.rotation)} degrees!"
        transform = CVAffineTransform(scale=1, rotation=0, shear=0, translation=transform.translation)  # Coerce scale and rotation
        transform = transform.toPartialMatrix()
        return transform

    @staticmethod
    def _applyTransform(transform: np.ndarray, measurement: ITOMeasurement):
        logger = logging.getLogger(__name__)
        logger.debug(f"Starting data transformation of {measurement.name}")
        im = measurement.analysisResults.meanReflectance
        tform = cv2.invertAffineTransform(transform)
        meanReflectance = cv2.warpAffine(im, tform, im.shape, borderValue=-666.0, flags=cv2.INTER_NEAREST)  # Blank regions after transform will have value -666, can be used to generate a mask.
        mask = meanReflectance == -666.0
        mask = binary_dilation(mask)  # Due to interpolation we sometimes get weird values at the edge. dilate the mask so that those edges get cut off.
        kcube = measurement.analysisResults.reflectance
        reflectance = np.zeros_like(kcube.data)
        for i in range(kcube.data.shape[2]):
            reflectance[:, :, i] = cv2.warpAffine(kcube.data[:, :, i], tform, kcube.data.shape[:2]) + meanReflectance
        measurement.analysisResults.releaseMemory()
        reflectance[mask] = np.nan
        return reflectance


class Analyzer:
    """
    Takes raw data and analyzes it. First by establishing affine transforms from the template to the measurements
    and then by running a variety of "Scoring" routines that compare the template to the transformated measurement
    data.

    Args:
        loader: A data loader object that provides access to a `template` measurement and a sequence of `measurement`
            measurements.
        useCached: If `True` then load cached information about the affine transforms if available. Saves processing time.
        debugMode: Runs the data transform generator in debug mode. Plots will be opened that display the results of
            the transform generation.
        method: Selects which method the transform generator should use. All possible options are stored in the
            `TransformGenerator.Method` enum.
        blurSigma: This value sets the `sigma` of the gaussian blur that occurs at the beginning of the scoring process.
            Units are in pixels. See documentation for `TransformedDataScorer` for more information.
    """
    def __init__(self, loader: AbstractMeasurementLoader, useCached: bool = True, debugMode: bool = False,
                 method: TransformGenerator.Method = TransformGenerator.Method.XCORR, blurSigma: float = None):
        self.transformer = TransformedDataSaver(loader, useCached, debugMode, method)
        self.scorer = TransformedDataScorer(loader, 'score', blurSigma)
        self.output = self.scorer.output