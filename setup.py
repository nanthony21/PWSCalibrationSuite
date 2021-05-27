# Copyright 2018-2020 Nick Anthony, Backman Biophotonics Lab, Northwestern University
#
# This file is part of PWSpy.
#
# PWSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PWSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PWSpy.  If not, see <https://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
"""
This file is used to install the pws_calibration_suite package.
"""
from setuptools import setup, find_packages
import setuptools_scm

setup(name='pws_calibration_suite',
      version=setuptools_scm.get_version(write_to="src/pws_calibration_suite/version.py"),
      description='A collection of tools for PWS calibration.',
      author='Nick Anthony',
      author_email='nicholas.anthony@northwestern.edu',
      url='https://github.com/nanthony21/pws_calibration_suite',
      python_requires='>=3.7',
      install_requires=['numpy',
                        'matplotlib',
                        'pandas',
                        'h5py',
                        'jsonschema',
                        'opencv-python', #opencv is required but naming differences between conda and pip seem to cause issues. Maybe should be commented out?
                        'scikit-image',
                        'pwspy',
                        'mpl_qt_viz',
                        'py4j',
                        'pyqt5',
                        'qdarkstyle'
                        ],
      package_dir={'': 'src'},
      package_data={'pws_calibration_suite': ['_resources/*']},
      packages=find_packages('src')
	)
