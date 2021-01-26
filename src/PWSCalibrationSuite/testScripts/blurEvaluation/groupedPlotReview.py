from PyQt5.QtWidgets import QApplication
from PWSCalibrationSuite._utility import CVAffineTransform
from PWSCalibrationSuite.testScripts import experimentInfo
from PWSCalibrationSuite.testScripts.loader import Loader
import matplotlib.pyplot as plt
from mpl_qt_viz.visualizers import DockablePlotWindow
import pandas as pd
import numpy as np


def loadDataFrame(measurementSet: str) -> pd.DataFrame:
    loader = Loader(experimentInfo.workingDirectory, measurementSet, readOnly=True)
    scoreNames = loader.measurements[0].loadTransformedData(
        loader.template.idTag).getScoreNames()  # We assume that all measurements have the same score names.

    results = []
    for i in loader.measurements:
        try:
            result = i.loadTransformedData(loader.template.idTag)
        except OSError:
            result = None  # Calibration must have failed. wasn't saved.
        results.append(result)

    l = []
    l2 = []
    for result, measurement in zip(results, loader.measurements):
        if result is None:
            continue
        displacement = CVAffineTransform.fromPartialMatrix(result.affineTransform).translation
        displacement = np.sqrt(displacement[0] ** 2 + displacement[1] ** 2)
        l.append({'displacement': displacement, 'measurementName': measurement.name, 'measurement': measurement,
                  'result': result})

        scoreDict = {'measurementName': measurement.name}
        for scoreName in scoreNames:
            score = result.getScore(scoreName)
            scoreDict[f"{scoreName}_score"] = score
        l2.append(scoreDict)

    df = pd.DataFrame(l)
    df2 = pd.DataFrame(l2)

    df = pd.merge(df, df2, on='measurementName')
    df['experiment'] = df.apply(lambda row: row['measurementName'].split('_')[0], axis=1)
    df['setting'] = df.apply(lambda row: '_'.join(row['measurementName'].split('_')[1:]), axis=1)
    del df['measurementName']
    return df


def experimentPlot(df, title, dataFunc):
    fig, ax = expWindow.subplots(title=title, dockArea='top')
    ax: plt.Axes
    for expName, g in df.groupby('experiment'):
        g = g.sort_values('idx')
        scores = g.apply(dataFunc, axis=1)
        ax.scatter(g['idx'], scores, label=expName)
    labels = ['Aligned'] + [f"Setting{i+1}" for i in range(len(scores)-1)]  # We do this dynamically to accomodate changed in the data fed into the function.
    ax.set_xticks(g.idx)
    ax.set_xticklabels(labels)
    ax.legend()

if __name__ == '__main__':
    import matplotlib as mpl

    measurementSet = 'xcorr_cdr_sift_test'

    df = loadDataFrame(measurementSet)
    print("Loaded Dataframe")
    df = pd.merge(df, experimentInfo.experiment, on=('experiment', 'setting'))
    df['setting'] = df['setting'].apply(lambda val: val.replace('_', '.'))  # Replace the underscores with period to make the NA look better in plots

    df = df[df['experiment']!='centered'] # Its too confusing with this experiment

    scoreNames = [colName.split('_')[0] for colName in df.columns if colName.endswith("_score")]  # Assumes there is no '_' in the score name
    #Sort scorenames numerically
    scoreNameInts = [0 if x=='None' else int(x) for x in scoreNames]
    scoreNameInts, scoreNames = list(zip(*sorted(zip(scoreNameInts, scoreNames))))
    scoreName = '2'

    app = QApplication([])
    expWindow = DockablePlotWindow("Experiment Comparison")

    # Plot NRMSE Score
    experimentPlot(df, 'NRMSE', lambda row: row[f'{scoreName}_score'].nrmse.score)

    # Plot SSIM Score
    experimentPlot(df, 'SSIM', lambda row: row[f'{scoreName}_score'].ssim.score)

    # Plot LatXCorr Score
    experimentPlot(df, 'LatXCorr', lambda row: row[f'{scoreName}_score'].latxcorr.score)

    # Lateral CDR_x
    experimentPlot(df, 'LatXCorr CDR_x', lambda row: row[f'{scoreName}_score'].latxcorr.cdrX)

    # Lateral CDR_y
    experimentPlot(df, 'LatXCorr CDR_y', lambda row: row[f'{scoreName}_score'].latxcorr.cdrY)

    # Lateral CDR ratio (pseudo eccentricity)
    experimentPlot(df, 'LatXCorr XY Ratio', lambda row: row[f'{scoreName}_score'].latxcorr.cdrY / row[f'{scoreName}_score'].latxcorr.cdrX)

    # Plot AxXCorr Score
    experimentPlot(df, 'AxXCorr', lambda row: row[f'{scoreName}_score'].axxcorr.score)

    # Axial Shift
    experimentPlot(df, 'AxXcorr Shift', lambda row: row[f'{scoreName}_score'].axxcorr.shift)

    # Axial CDR
    experimentPlot(df, 'AxXcorr CDR', lambda row: row[f'{scoreName}_score'].axxcorr.cdr)

    # Reflectance
    experimentPlot(df, 'Reflectance', lambda row: row[f'{scoreName}_score'].reflectance.reflectanceRatio)

    # Score
    experimentPlot(df, 'Avg. Score', lambda row: row[f'{scoreName}_score'].score)

    app.exec()
    a = 1
