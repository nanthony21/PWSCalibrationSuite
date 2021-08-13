import numpy as np


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
