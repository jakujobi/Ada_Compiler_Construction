# JohnA1.py

import os
import re
import sys
from pathlib import Path

# Add the parent directory to the system path
repo_home_path = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_home_path))

from Modules.LexicalAnalyzer import LexicalAnalyzer