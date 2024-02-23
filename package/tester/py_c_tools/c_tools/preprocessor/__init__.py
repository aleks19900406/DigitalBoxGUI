"""Support for c files preprocessing

In order to perform a code parsing and analysis, c files must be preprocessed.
This module provides some :class:`basic support for preprocessing<c_tools.preprocessor.
Preprocessor>`, using `gcc` compiler.

It may also be ran as an executable module. execute the following for help::

    python -m c_tools.preprocessor --help
"""
from ._core import Preprocessor
