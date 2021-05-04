import subprocess
from time import time

from py4j.java_gateway import JavaGateway
import py4j
import pathlib as pl
import os


class MMGate:
    def __init__(self):
        self._mmProc = None
        self._gw = self.mm = self.pws = None
        self._connected = False

    def isConnected(self) -> bool:
        return self._connected

    def openMM(self, installDir: str):
        if self._connected:
            raise ValueError("Already connected to PWS Micro-Manager")
        installPath = pl.PurePath(installDir)
        os.chdir(installPath)  # If we don't do this then the plugins won't be found by micro-manager.
        self._mmProc = subprocess.Popen(str(installPath / 'imagej.exe'), stdout=subprocess.PIPE, shell=True)

    def connect(self, timeout: float = 20):
        if self._connected:
            raise ValueError("Already connected to PWS Micro-Manager")

        sTime = time()
        connected = False
        while time() - sTime < timeout:
            try:
                self._gw = JavaGateway()
                self.mm = self._gw.entry_point
                self.mm.logs()  # Just testing for connection
            except py4j.protocol.Py4JNetworkError as e:
                continue
            connected = True
            break
        if not connected:
            raise TimeoutError(f"Failed to connect to Micro-Manager in {timeout} seconds")

        plugs = self.mm.plugins().getMenuPlugins()
        pwsPlug = plugs['edu.bpl.pwsplugin.PWSPlugin']
        assert pwsPlug is not None
        self.pws = pwsPlug.api()
        self._connected = True

    def close(self):
        # disconnect
        pass

if __name__ == '__main__':



    a = 1