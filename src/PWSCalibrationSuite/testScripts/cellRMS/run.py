import logging
import sys
from PWSCalibrationSuite.testScripts.cellRMS import loadDataFrame


def configureLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


if __name__ == '__main__':
    logger = configureLogger()
    measurementSet = 'xcorr_cdr_test'
    df = loadDataFrame(measurementSet, '2', fromCache=False)
    a = 1
