import logging
import sys
from PWSCalibrationSuite.testScripts.cellRMS import loadDataFrame


def configureLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


if __name__ == '__main__':
    import seaborn as sns
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    plt.ion()

    logger = configureLogger()
    measurementSet = 'xcorr_cdr_test'
    df = loadDataFrame(measurementSet, '2', fromCache=True)

    anyRoiClipped = df.groupby(['cellNum', 'roiNum']).apply(lambda g: np.any(g['roiClipped']))  # True if any of the matching 'cellNum', 'roiNum' rois are clipped.
    anyRoiClipped.name = 'anyRoiClipped'  # needed for the merge
    df = pd.merge(df, anyRoiClipped, left_on=['cellNum', 'roiNum'], right_index=True)

    df = df[~df['anyRoiClipped']]  # Remove any cells that have some faulty rois

    # Aligned stability
    df2 = df.loc[:, ['experiment', 'setting', 'cellNum', 'roiNum', 'rms', 'reflectance', 'isref', 'anyRoiClipped']]
    df2 = df2[df2['isref']]
    ref = df2[(df2['experiment'] == 'centered') & (df2['setting'] == '0_52')].set_index(['cellNum', 'roiNum'])
    for param in['rms', 'reflectance']:
        pChange = df2.groupby(['cellNum', 'roiNum']).apply(lambda g: 100 * (g[param] - ref.loc[g.name][param]) / ref.loc[g.name][param])
        pChange.index = pChange.index.get_level_values(-1)
        newName = f'% Change {param}'
        df2[newName] = pChange
        fig, ax = plt.subplots()
        fig.suptitle(f"Aligned Stability of {param}")
        sns.boxplot(data=df2, x='experiment', y=newName)
        # sns.scatterplot(data=df2, x='experiment', y=newName)

    # Calculate percent change of rms and reflectance
    df2 = df.loc[:, ['experiment', 'setting', 'cellNum', 'roiNum', 'rms', 'reflectance', 'isref']]
    df2['condition'] = df2.apply(lambda row: f"{row['experiment']}.{row['setting']}", axis=1)
    ref = df2[(df2['experiment'] == 'centered') & (df2['setting'] == '0_52')].set_index(['cellNum', 'roiNum'])
    for param in ['rms', 'reflectance']:
        df3 = df2.copy()
        pChange = df3.groupby(['experiment', 'cellNum', 'roiNum']).apply(lambda g: 100 * (g[param] - g[g.isref].iloc[0][param]) / g[g.isref].iloc[0][param])
        pChange.index = pChange.index.get_level_values(-1)
        newName = f'pChange_{param}'
        df3[newName] = pChange
        df3 = df3[~df3['isref']]  # Data is normalized by the references so don't bother plotting them.
        # fig, ax = plt.subplots()
        # sns.boxplot(data=df3, x='condition', y=newName)
        # plt.xticks(rotation=30)
        fig, axs = plt.subplots(ncols=3, sharey=True)
        fig.suptitle(f"% Change {param.upper()}")
        for i, (expName, g) in enumerate(df3.groupby('experiment')):
            ax = axs[i]
            sns.boxplot(data=g, x='setting', y=newName, ax=ax)
            ax.set(ylabel=None, xlabel=expName)
            ax.grid(axis='y')
        plt.subplots_adjust(wspace=0)

    a = 1
