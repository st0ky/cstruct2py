__version__ = "0.0.1"
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pycparser"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcpp"))
import pycparser
import pcpp

__all__ = ["pycbase", "pycarray", "pycstruct", "pycunion", "c2py", "basics"]
from . import *