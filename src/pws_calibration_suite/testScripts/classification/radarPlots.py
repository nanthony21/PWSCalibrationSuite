"""
Instead of decision trees can we just use a euclidean distance between feature values?
"""
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler


saveScaler = False  # If `True` then save scaler model to file for later use.

def make_spider(pandasRow: pd.Series, title: str, color: str, rMax: float = None):
    """Alternative copied from https://python-graph-gallery.com/392-use-faceting-for-radar-chart"""
    # number of variable
    categories = list(pandasRow.index)
    N = len(categories)

    # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    # Initialise the spider plot
    fig = plt.figure()
    ax = plt.subplot(polar=True)

    # If you want the first axis to be on top:
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Draw one axe per variable + add labels labels yet
    plt.xticks(angles[:-1], categories, color='grey', size=8)

    # Draw ylabels
    ax.set_rlabel_position(0)
    rMax = max(pandasRow) if rMax is None else rMax
    plt.ylim(0, rMax)

    # Ind1
    values = pandasRow.values.flatten().tolist()
    values += values[:1]
    ax.plot(angles, values, color=color, linewidth=2, linestyle='solid')
    ax.fill(angles, values, color=color, alpha=0.4)

    # Add a title
    plt.title(title, size=11, y=1.1)
    return fig, ax


if __name__ == '__main__':
    from pws_calibration_suite.testScripts.classification import generateFeatures, loadDataFrame
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.ion()

    measurementSet = 'xcorr_blurScan_4'
    scoreName = '2'
    print("Starting frame load")
    df = loadDataFrame(measurementSet, scoreName)
    print("Loaded frame")

    inputs = generateFeatures(df)
    inputCols = inputs.columns

    df = pd.merge(df, inputs, right_index=True, left_index=True)

    scaler = StandardScaler()
    scaler.fit(df[inputCols][df['isref']])
    df[inputCols] = (scaler.transform(df[inputCols]))/100 + 1  # the 100 is totally arbitrary here. The +1 is because if the values are centered around 0 they won't show up on the radar plot well.
    print(scaler.scale_, scaler.mean_)


    avgRefCoord = np.ones((len(inputCols),))#df[df['isref']][inputCols].mean()
    df['distance'] = df.apply(lambda row: np.sqrt(((avgRefCoord - row[inputCols])**2).sum()), axis=1)

    for i, row in df.iterrows():
        color = 'blue' if row['isref'] else 'red'
        # euclideanDistance = np.sqrt(((avgRefCoord - row[inputCols])**2).sum())
        title = f"{row['experiment']}, {row['setting']}, Distance: {row['distance']:.2f}"
        make_spider(row[inputCols].abs(), title=title, color=color, rMax=1.6)  # We do absolute value here since the axial shift can be negative which messes up the plots. The scaling of values needs to be changed before this is done.

    df['(Experiment / Setting)'] = df.apply(lambda row: (row['experiment'], row['setting']), axis=1)
    df = df.sort_values('isref', ascending=False)
    plt.figure()
    ax: plt.Axes = sns.barplot(data=df, x="(Experiment / Setting)", y='distance')

    for p, (i, row) in zip(ax.patches, df.iterrows()):  # Mark the references as green
        if row['isref']:
            p.set_color('green')
    plt.xticks(rotation=20)

    if saveScaler:
        import joblib
        joblib.dump(scaler, 'scaler.sklearn')

    a = 1
