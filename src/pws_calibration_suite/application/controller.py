from __future__ import annotations
import logging
import shutil
import time

from pws_calibration_suite.application.javaGate._image import Image
from pws_calibration_suite.application.javaGate._mmGate import MMGate
from pws_calibration_suite.loader import DefaultLoader
import pathlib as pl


class Controller:
    def __init__(self, gate: MMGate):
        self._mmGate = gate
        self.im = None

    def getGate(self) -> MMGate:
        return self._mmGate

    def snap(self) -> Image:  # TODO this was just for testing. With how the program is now structured it would make more sense as a `RoutinePlugin` example.
        im = self._mmGate.mm.live().snap(False)[0]
        self.im = Image.fromJava(im)
        return self.im


