from PWSCalibrationSuite.testScripts import experimentInfo
from PWSCalibrationSuite.testScripts.loader import Loader
import pandas as pd
import numpy as np


def loadDataFrame(measurementSet: str, scoreName: str) -> pd.DataFrame:
    loader = Loader(experimentInfo.workingDirectory, measurementSet, readOnly=True)
    results = []
    for i in loader.measurements:
        try:
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
    return df


def generateFeatures(rawDf: pd.DataFrame):
    # Split the `CombinedScore` object into numerical columns that will be used as inputs
    funcDict = {
        'latXCorr': lambda row: row.score.latxcorr.score,
        'latXCorr_cdr': lambda row: np.sqrt((row.score.latxcorr.cdrY**2 + row.score.latxcorr.cdrX**2)/2),  # RMS of cdrx and cdry. Looking at data by eye this didn't look that useful, I'm inclined to get rid of it.
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
