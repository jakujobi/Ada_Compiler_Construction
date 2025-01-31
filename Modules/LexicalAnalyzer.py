# LexicalAnalyzer
# LexicalAnalyzer is a module that provides a lexical analyzer for Ada programs.



import os
import sys
from typing import List, Optional

from pathlib import Path

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.FileHandler import FileHandler
from Modules.Token import Token
from Modules.Definitions import Definitions