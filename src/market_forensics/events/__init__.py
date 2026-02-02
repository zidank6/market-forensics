"""Event detection modules."""

from .detector import (
    DetectorError,
    detect_price_shocks,
    detect_price_shocks_from_config,
)

__all__ = [
    "detect_price_shocks",
    "detect_price_shocks_from_config",
    "DetectorError",
]
