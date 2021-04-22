import os

from pws_calibration_suite.testScripts import experimentInfo
from pws_calibration_suite.testScripts.loader import Loader
import pandas as pd
import numpy as np
import pwspy.dataTypes as pwsdt
from glob import glob
from pwspy.analysis.compilation import PWSRoiCompiler, PWSCompilerSettings, GenericCompilerSettings, GenericRoiCompiler
import logging


def loadDataFrame(measurementSet: str, scoreName: str, fromCache: bool = True) -> pd.DataFrame:
    loader = Loader(experimentInfo.workingDirectory, measurementSet, readOnly=True)
    results = []
    for i in loader.measurements:
        try:
            logging.getLogger(__name__).info(f"Load transformed data {i.name}")
            result = i.loadTransformedData(loader.template.idTag)
        except OSError:
            result = None  # Calibration must have failed. wasn't saved.
        results.append(result)

    l = []
    for result, measurement in zip(results, loader.measurements):
        if result is None:
            continue

        scoreNames = loader.measurements[0].loadTransformedData(
            loader.template.idTag).getScoreNames()  # We assume that all measurements have the same score names.
        assert scoreName in scoreNames, f"Score `{scoreName}` not available. Available: {scoreNames}"
        l.append({'measurementName': measurement.name, 'measurement': measurement, 'result': result, 'score': result.getScore(scoreName)})

    df = pd.DataFrame(l)
    df['experiment'] = df.apply(lambda row: row['measurementName'].split('_')[0], axis=1)
    df['setting'] = df.apply(lambda row: '_'.join(row['measurementName'].split('_')[1:]), axis=1)
    del df['measurementName']
    df = pd.merge(df, experimentInfo.experiment, on=('experiment', 'setting'))
    logging.getLogger(__name__).info(f"Start loading cell data DataFrame")
    cellDf = loadCellData(fromCache)
    logging.getLogger(__name__).info(f"Finished loading cell data DataFrame")
    df = pd.merge(df, cellDf, on=('experiment', 'setting'))
    return df


def loadCellData(fromCache: bool = True):
    cachePath = os.path.join(experimentInfo.workingDirectory, 'cellDataCache.h5')
    if fromCache and os.path.exists(cachePath):
        return pd.read_hdf(cachePath, key='data')
    l = []
    anName = 'script'
    pwsCompiler = PWSRoiCompiler(
        PWSCompilerSettings(reflectance=True, rms=True)
    )
    genCompiler = GenericRoiCompiler(
        GenericCompilerSettings(roiArea=True)
    )
    for i, row in experimentInfo.experiment.iterrows():
        exp = row['experiment']
        setting = row['setting']
        pth = os.path.join(experimentInfo.workingDirectory, exp, setting, 'cells')
        for filePath in glob(os.path.join(pth, "Cell[0-9]")):
            acq = pwsdt.AcqDir(filePath)
            try:
                anls = acq.pws.loadAnalysis(anName)
            except OSError:
                print(f"Skipping {filePath}. No analysis")
                continue
            for roiName, roiNum, fformat in acq.getRois():
                roi = acq.loadRoi(roiName, roiNum, fformat)
                compResults, warnings = pwsCompiler.run(anls, roi)
                roiResults = genCompiler.run(roi)
                [print(warn.longMsg) for warn in warnings]
                l.append({
                    'experiment': exp,
                    'setting': setting,
                    'cellNum': acq.getNumber(),
                    'roiNum': roiNum,  # All names are NUC so no need to store that.
                    'rms': compResults.rms,
                    'reflectance': compResults.reflectance,
                    'roiSize': roiResults.roiArea
                    })
    df = pd.DataFrame(l)
    # detect ROIS that are of different size than their counterparts.
    deltaSize = df.groupby(['cellNum', 'roiNum']).apply(lambda group: (group['roiSize'] - group['roiSize'].max())/group['roiSize'].max()*100)  # Percent difference from maximum roi of that same group. indicates how much may have been clipped due to translation.
    deltaSize.index = deltaSize.index.get_level_values(-1)  # Restore the main index
    df['roiClipped'] = deltaSize.abs() >= 5  # A little bit of clipping is probably ok. Mark rois with more that 5% of area lost
    df.to_hdf(cachePath, mode='w', key='data')
    return df


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