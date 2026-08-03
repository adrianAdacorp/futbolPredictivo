"""Ajuste de path para ejecutar scripts desde scripts/ (encuentra la raíz)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
