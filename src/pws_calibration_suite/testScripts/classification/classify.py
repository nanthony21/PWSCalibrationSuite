import pandas as pd
# import graphviz
import matplotlib.pyplot as plt
import os

from pws_calibration_suite.testScripts.classification import loadDataFrame, generateFeatures


def viewTree(decTree, featNames, classNames, title='temp'):
    fig = plt.figure()
    fig.suptitle(title)
    tree.plot_tree(decTree,
                   feature_names=featNames,
                   class_names=[str(i) for i in classNames],
                   filled=True)

    # dot_data = tree.export_graphviz(decTree, out_file=None,
    #     feature_names=featNames,
    #     class_names=classNames,
    #     filled=True, rounded=True,
    #     special_characters=True)
    # graph = graphviz.Source(dot_data)
    # sfx = 0
    # while os.path.exists(f"{title}_{sfx}.png"):  # Without this auto-renaming the `view` option causes all calls to show the same image (the last one)
    #     sfx += 1
    # fullPath = f"{title}_{sfx}.png"
    # graph.render(filename=fullPath, format='png', view=True)


if __name__ == '__main__':
    from sklearn import tree
    from sklearn.multioutput import MultiOutputClassifier
    import numpy as np
    plt.ion()

    measurementSet = 'xcorr_blurScan_4'
    scoreName = '2'
    print("Starting frame load")
    df = loadDataFrame(measurementSet, scoreName)
    print("Loaded frame")

    inputs = generateFeatures(df)
    inputCols = inputs.columns

    # In this case we have a `multilabel` (not `multiclass`) situation. (see: https://scikit-learn.org/stable/modules/multiclass.html)
    # Decision trees are inherently multiclass but we can get multilabel functionality with `MultiOutputClassifier` (which internally creates a tree for each label.
    # 3 Classes
    outputs = pd.DataFrame(
        {'apertureCentered': (df['experiment'] != 'translation') |
                               ((df['experiment'] == 'translation') & df['isref']),
        'naCorrect': (df['experiment'] != 'centered') |
                        ((df['experiment'] == 'centered') & df['isref']),
        "fieldStopCorrect": (df['experiment'] != 'fieldstop') |
                                ((df['experiment'] == 'fieldstop') & df['isref'])
        })
    outputs['isref'] = df.isref
    mlTree = MultiOutputClassifier(tree.DecisionTreeClassifier())
    mlTree.fit(inputs, outputs)
    for labelName, clsfr in zip(outputs.columns, mlTree.estimators_):
        viewTree(clsfr, inputCols, [f"not_{labelName}", labelName], title=labelName)

    # 5 Classes. We want multilabel, except that the three aperture classes are mutually exclusive (multiclass)
    def determineAperture(row):
        if (row['settingQuantity'] > 0.52) & (row['experiment'] == 'centered'):
            return 'apertureBig'
        elif (row['experiment'] == 'centered') & (row['settingQuantity'] < 0.52):
            return 'apertureSmall'
        else:
            return 'naCorrect'

    outputs = [
        pd.DataFrame({'apertureCentered': (df['experiment'] != 'translation') |
                                ((df['experiment'] == 'translation') & df['isref'])}),
        pd.DataFrame({'na': df.apply(determineAperture, axis=1)}),
        pd.DataFrame({"fieldStopCorrect": (df['experiment'] != 'fieldstop') |
                                ((df['experiment'] == 'fieldstop') & df['isref'])})
    ]

    for output in outputs:
        clsfr = tree.DecisionTreeClassifier()
        clsfr.fit(inputs, output)
        viewTree(clsfr, inputCols, clsfr.classes_, title=output.columns[0])

    a = 1
