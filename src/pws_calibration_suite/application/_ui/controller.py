from __future__ import annotations
import logging
import shutil
import time
import numpy as np
from pws_calibration_suite.application._javaGate import MMGate
from pws_calibration_suite.loader import DefaultLoader
import pathlib as pl


class Controller:
    def __init__(self, gate: MMGate):
        self._mmGate = gate
        self.im = None

    def getGate(self) -> MMGate:
        return self._mmGate

    def acquire(self, path: pl.Path, simulated: bool = False) -> DefaultLoader:
        """
        Command the acquisition software to acquire a sequence acquisition.

        Args:
            path: The file path to save the data to.
            simulated: If `True` then existing data is loaded without actually having the acquisition software run anything.

        Returns:
            A `Loader` object to provide access to the acquired data.
        """
        logger = logging.getLogger(__name__)
        logger.debug("Starting acquisition.")
        if not simulated:
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
        logger.debug("Loading.")
        loader = DefaultLoader(path)
        logger.debug("Done loading.")
        return loader

    def snap(self) -> Image:
        im = self._mmGate.mm.live().snap(False)[0]
        self.im = Image.fromJava(im)
        return self.im


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
