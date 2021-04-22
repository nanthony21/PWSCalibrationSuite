
from pws_calibration_suite.testScripts import experimentInfo
from pws_calibration_suite.testScripts.classification import generateFeatures, loadDataFrame
from pws_calibration_suite.testScripts.loader import Loader
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

    plt.ion()

    measurementSet = 'xcorr_cdr_sift_test'
    print("Start loading frame")
    df = loadDataFrame(measurementSet, '2')
    print("Finished loading frame")
    feats = generateFeatures(df)
    inputCols = feats.columns

    # w = DockablePlotWindow("Feature Correlation")
    # for c1, c2 in itertools.combinations(inputCols, 2):
    #     fig, ax = w.subplots(f"{c1} : {c2}")
    #     ax.scatter(feats[c1], feats[c2])
    #     ax.set_xlabel(c1)
    #     ax.set_ylabel(c2)



    #Plot normalized correlations
    normFeats = (feats - feats.mean(axis=0)) / feats.std(axis=0)  # Note: the sklearn.StandardScaler uses a biased stdDev so doesn't work well for getting correlations of 1.
    pca = PCA(svd_solver='full')
    pca.fit(normFeats)

    import seaborn as sns
    plt.figure()
    sns.pairplot(normFeats)  # Nice view of correlations



    plt.figure()
    sns.set(font_scale=1)
    hm = sns.heatmap(pca.get_covariance(),
                     cbar=True,
                     annot=True,
                     square=True,
                     fmt='.2f',
                     annot_kws={'size': 12},
                     cmap='coolwarm',
                     yticklabels=inputCols,
                     xticklabels=inputCols)
    plt.title('Covariance matrix showing correlation coefficients', size=18)

    # PCA
    pipe = pipeline.make_pipeline(StandardScaler(), PCA(svd_solver='full', n_components='mle'))
    pipe.fit(feats)
    print("PCA Reccomended components: ", pipe.named_steps['pca'].n_components_)



    a = 1

