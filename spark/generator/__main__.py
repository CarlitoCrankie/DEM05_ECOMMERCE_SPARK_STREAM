"""
Generator package entry point
Allows running as: python3 -m generator
"""
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.data_generator import run_generator

if __name__ == "__main__":
    run_generator()