"""
E-Commerce Data Generator Package
Handles streaming event generation with retry logic and logging
"""

from .data_generator import run_generator
__all__ = ["run_generator"]