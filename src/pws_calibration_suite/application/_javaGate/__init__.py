import subprocess
from time import time

from py4j.java_gateway import JavaGateway
import py4j
import pathlib as pl
import os


class MMGate:
    """
    Responsible for interacting with Micro-Manager.

    Attributes:
        _mmProc: A subprocess.Popen instance corresponding to the process running Micro-Manager.
        _gw: The `gateway` that communicates to Java layer of Micro-Manager.
        mm: Reference to the Java `MMStudio` instance. Main API entry point of the application
        pws: Reference to the Java `PWSPlugin` instance.
        _connected: Keeps track of if we are connected with the Java gate.
    """
    def __init__(self):
        self._mmProc: subprocess.Popen = None
        self._gw = self.mm = self.pws = None
        self._connected: bool = False

    def isConnected(self) -> bool:
        return self._connected

    def openMM(self, installDir: str = r'C:\Program Files\PWSMicroManager'):
        """
        Open a new instance of Micro-Manager and connect to it.
        Args:
            installDir: The installation directory of Micro-Manager that we want to open.

        Raises:
            If we are already connected to an instance of Micro-Manager a RuntimeError will be raised.

        """
        if self._connected:
            raise RuntimeError("Already connected to PWS Micro-Manager")
        installPath = pl.PurePath(installDir)
        os.chdir(installPath)  # If we don't do this then the plugins won't be found by micro-manager.
        self._mmProc = subprocess.Popen(str(installPath / 'imagej.exe'), stdout=subprocess.PIPE, shell=True)
        self.connect()

    def connect(self, timeout: float = 20):
        """
        Connect the JavaGateWay to the Py4J server included in PWS Micro-Manager

        Args:
            timeout: If connection isn't established within this many seconds then a TimeoutError will be raised.
        """
        if self._connected:
            raise ValueError("Already connected to PWS Micro-Manager")

        sTime = time()
        connected = False
        while time() - sTime < timeout:
            try:
                self._gw = JavaGateway()
                self.mm = self._gw.entry_point
                self.mm.logs()  # Just testing for sucessful connection
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
        """
        Disconnect the JavaGateway and set attributes back to `None`.

        """
        self._gw = self.mm = self.pws = None
        self._connected = False


if __name__ == '__main__':



    a = 1