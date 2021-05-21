import logging
import os
import shutil
import time
from typing import Callable
import numpy as np
import pwspy
from pws_calibration_suite._javaGate import MMGate
from pws_calibration_suite.comparison.analyzer import Analyzer
from pws_calibration_suite.loader import DefaultLoader
import pathlib as pl


class Controller:
    def __init__(self, gate: MMGate):
        self._mmGate = gate
        self.im = None

    def getGate(self) -> MMGate:
        return self._mmGate

    def acquire(self, path: pl.Path) -> DefaultLoader:
        from pws_calibration_suite import calibrationSequenceFile
        sequencerapi = self._mmGate.pws.sequencer()
        sequencerapi.loadSequence(str(calibrationSequenceFile))
        if path.exists():
            shutil.rmtree(path)
        path.mkdir()
        sequencerapi.setSavePath(str(path))
        sequencerapi.runSequence()
        while sequencerapi.isSequenceRunning():
            time.sleep(.5)

        loader = DefaultLoader(path)
        return loader

    def snap(self):
        im = self._mmGate.mm.live().snap(False)[0]
        self.im = Image.fromJava(im)
        import matplotlib.pyplot as plt
        plt.imshow(self.im.arr)


class Image:
    def __init__(self, arr: np.ndarray):
        assert isinstance(arr, np.ndarray)
        self.arr = arr

    @classmethod
    def fromJava(cls, im):
        buf = im.getByteArray()
        dtype = np.dtype('>i1') if im.getBytesPerPixel() == 1 else np.dtype('>i2')
        arr = np.frombuffer(buf, dtype=dtype)
        arr = arr.reshape((im.getHeight(), im.getWidth()))
        return cls(arr)
