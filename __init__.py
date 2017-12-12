__version__ = "0.0.1"
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "pycparser"))
sys.path.append(os.path.join(os.path.dirname(__file__), "pcpp"))
import pycparser
import pcpp

import pycbase
import basics
import pycstruct
import pycunion
import pycarray
import c2py
