import logging
import os
import time
from typing import Callable
import numpy as np
import pwspy
from pws_calibration_suite._javaGate import MMGate

class Controller:
    def __init__(self, gate: MMGate):
        self._mmGate = gate
        self.im = None

    def getGate(self) -> MMGate:
        return self._mmGate

    def acquire(self, path: os.PathLike):
        from pws_calibration_suite import calibrationSequenceFile
        sequencerapi = self._mmGate.pws.sequencer()
        sequencerapi.loadSequence(str(calibrationSequenceFile))
        sequencerapi.setSavePath(str(path))
        sequencerapi.runSequence()
        time.sleep(1)  # TODO It takes a while for `isSequenceRunning` to return flse, must pause a little.
        while sequencerapi.isSequenceRunning():
            time.sleep(1)
        seq, acqs = pwspy.utility.acquisition.loadDirectory(str(path))
        ito, reflectance, glass, scatter = acqs

        # loader = Loader()
        # Analyzer(loader, blurSigma=7)

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
