"""
yandex-panorama-downloader
~~~~~~~~~~~~~~~~~~~~~~~~~
A high-performance downloader for Yandex Maps 360° street view and indoor panoramas.
"""

from .models import Panorama, Size, Link, Place, Address
from .api import (
    find_panorama,
    find_panorama_async,
    find_panorama_by_id,
    find_panorama_by_id_async,
)
from .downloader import download_panorama, download_panorama_async
from .url_parser import parse_target, TargetInfo

__version__ = "0.1.0"

__all__ = [
    "Panorama",
    "Size",
    "Link",
    "Place",
    "Address",
    "find_panorama",
    "find_panorama_async",
    "find_panorama_by_id",
    "find_panorama_by_id_async",
    "download_panorama",
    "download_panorama_async",
    "parse_target",
    "TargetInfo",
    "__version__",
]
