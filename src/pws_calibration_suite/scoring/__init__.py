import pandas as pd
import numpy as np


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