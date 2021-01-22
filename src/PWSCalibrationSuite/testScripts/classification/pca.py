
from PWSCalibrationSuite.testScripts import experimentInfo
from PWSCalibrationSuite.testScripts.classification import generateFeatures, loadDataFrame
from PWSCalibrationSuite.testScripts.loader import Loader
import numpy as np
import pandas as pd
import os

if __name__ == '__main__':
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn import pipeline
    import matplotlib.pyplot as plt
    from mpl_qt_viz.visualizers import DockablePlotWindow
    import itertools

    measurementSet = 'xcorr_test'
    print("Start loading frame")
    df = loadDataFrame(measurementSet, '2')
    print("Finished loading frame")
    feats = generateFeatures(df)
    inputCols = feats.columns

    w = DockablePlotWindow("Feature Correlation")
    for c1, c2 in itertools.combinations(inputCols, 2):
        fig, ax = w.subplots(f"{c1} : {c2}")
        ax.scatter(feats[c1], feats[c2])
        ax.set_xlabel(c1)
        ax.set_ylabel(c2)

    scaler = StandardScaler()

    #Plot normalized correlations
    normFeats = (feats - feats.mean(axis=0)) / feats.std(axis=0)  # Note: the sklearn.StandardScaler uses a biased stdDev so doesn't work well for getting correlations of 1.
    pca = PCA(svd_solver='full')
    pca.fit(normFeats)
    fig, ax = plt.subplots()
    fig.suptitle("Feature Normalized X-Correlation")
    plt.imshow(pca.get_covariance(), clim=(-1, 1), cmap='bwr')
    plt.colorbar()
    tickLabels = ['trash'] + list(inputCols)  # I'm not sure why, but this is necessary.
    ax.set_xticklabels(tickLabels)
    ax.set_yticklabels(tickLabels)
    plt.xticks(rotation=20)

    # PCA
    pipe = pipeline.make_pipeline(StandardScaler(), PCA(svd_solver='full', n_components='mle'))
    pipe.fit(feats)
    print("PCA Reccomended components: ", pipe.named_steps['pca'].n_components_)



    a = 1