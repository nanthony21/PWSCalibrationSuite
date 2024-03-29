# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 17:08:42 2020

@author: backman05
"""
from pws_calibration_suite.comparison.TransformGenerator import TransformGenerator
from pws_calibration_suite.comparison.analyzer import Analyzer, TransformedDataSaver, TransformedDataScorer
from pws_calibration_suite.testScripts.loader import Loader
from importlib import reload
import logging
reload(logging)  # This prevents the sys.stdout handler from being added mlutiple times when we re-run the script in spyder.
import sys
import time


def configureLogger():
    logger = logging.getLogger()  # We get the root logger so that all loggers in pwspy will be handled.
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-4s %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from pws_calibration_suite.testScripts import experimentInfo
    plt.ion()
    logger = configureLogger()
    measurementSet = 'xcorr_cdr_sift_test'
    loader = Loader(experimentInfo.workingDirectory, measurementSet)
    transformer = TransformedDataSaver(loader, useCached=True, debugMode=True, method=TransformGenerator.Method.SIFT)

    # CLear all existing scores.
    for m in loader.measurements:
        tData = m.loadTransformedData(loader.template.idTag)
        tData.clearScores()

    # Start scoring.
    for blur in [2]:
        logger.info(f"Starting blur {blur}")
        stime = time.time()
        scorer = TransformedDataScorer(loader, str(blur), blurSigma=blur,
                                       parallel=True)
        logger.info(f"Total score time: {time.time() - stime}")
    a = 1  # BreakPoint
