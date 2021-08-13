import pathlib as pl
resourcesPath = pl.Path(__file__).parent / '_resources'
calibrationSequenceFile = resourcesPath / 'calibration.pwsseq'
from ._plugin import MyRoutine