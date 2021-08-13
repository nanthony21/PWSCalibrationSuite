from __future__ import annotations
import abc
from PyQt5.QtWidgets import QWidget
from mpl_qt_viz.visualizers import DockablePlotWindow

from pws_calibration_suite.application.controller import Controller
import typing as t_
import pws_calibration_suite.application.calibrationRoutines


class RoutinePlugin(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def instantiate(cls, controller: Controller, visualizer: DockablePlotWindow) -> RoutinePlugin:
        """Static method to create an instance of this routine plugin."""
        pass

    @abc.abstractmethod
    def getName(self) -> str:
        """Get the name to label this routine with"""
        pass

    @abc.abstractmethod
    def run(self):
        """Begin the measurement routine"""
        pass


class RoutinePluginManager:
    """A utility class to help manage RoutinePlugins"""

    def __init__(self, controller: Controller, visualizer: DockablePlotWindow, parentWidget: QWidget):
        pluginClasses = self._findPlugins()
        self._plugins: t_.List[RoutinePlugin] = [clazz.instantiate(controller, visualizer) for clazz in pluginClasses]
        self._controller = controller
        self._parentWidget = parentWidget

    def _findPlugins(self):
        """Scans the contents of pwspy_guiPWSAnalysisApp.plugins for any modules containing subclasses of CellSelectorPlugin.
        If someone wants to add a plugin without modifying this source code they can use namespace packages to make
        it seem as though their plugin module is in pwspy_guiPWSAnalysisApp.plugins"""
        import pkgutil, importlib, inspect
        # Based on something I saw here https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
        iter_namespace = lambda pkg: pkgutil.iter_modules(pkg.__path__, pkg.__name__ + ".")
        plugins = []
        # Find all submodules of the root module
        for finder, name, ispkg in iter_namespace(pws_calibration_suite.application.calibrationRoutines):
            mod = importlib.import_module(name)
            # Get all the classes that are defined in the module
            clsmembers = inspect.getmembers(mod, lambda member: inspect.isclass(member) and not inspect.isabstract(member))
            for name, cls in clsmembers:
                if issubclass(cls, RoutinePlugin):
                    plugins.append(cls)  # Add any class that implements the plugin base class
        return plugins

    def getPlugins(self) -> t_.Sequence[RoutinePlugin]:
        return self._plugins
