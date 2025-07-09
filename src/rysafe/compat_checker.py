"""Version and package compatibility validation."""

import importlib.metadata
import sys

from packaging.version import parse as parse_version


def guard_async_feature():
    """Prevent async usage in incompatible versions."""
    if sys.version_info < (3, 7):
        raise RuntimeError("Async requires Python 3.7+")


def validate_package(pkg: str, min_v: str, max_v: str):
    """
    Enforce package version constraints.

    Args:
        pkg: Package name
        min_v: Minimum version
        max_v: Maximum version

    Raises:
        ImportError: Version outside range
    """
    try:
        current = parse_version(importlib.metadata.version(pkg))
    except importlib.metadata.PackageNotFoundError:
        raise ImportError(f"{pkg} not installed")

    if not (parse_version(min_v) <= current <= parse_version(max_v)):
        raise ImportError(f"{pkg} version {current} outside allowed range")


def check_python_version():
    """Verify Python version compatibility."""
    if not (3, 8) <= sys.version_info[:2] <= (3, 13):
        raise RuntimeError(
            f"Python {sys.version_info.major}.{sys.version_info.minor} "
            f"not supported. Requires 3.8-3.13"
        )
