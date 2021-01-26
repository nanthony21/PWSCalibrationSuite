from PWSCalibrationSuite.testScripts.cellRMS import loadDataFrame

if __name__ == '__main__':
    measurementSet = 'xcorr_cdr_test'
    df = loadDataFrame(measurementSet, '2')
    a = 1
