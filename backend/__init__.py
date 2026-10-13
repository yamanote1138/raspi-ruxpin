"""Raspi Ruxpin backend package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("raspi-ruxpin")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
