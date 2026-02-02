"""Event detection modules."""

from .detector import (
    DetectorError,
    detect_price_shocks,
    detect_price_shocks_from_config,
)
from .ordering import (
    EventOrdering,
    OnsetDetection,
    OnsetType,
    OrderingError,
    analyze_all_orderings,
    analyze_event_ordering,
    analyze_event_ordering_from_config,
    save_orderings,
    save_orderings_csv,
    save_orderings_json,
)

__all__ = [
    "DetectorError",
    "EventOrdering",
    "OnsetDetection",
    "OnsetType",
    "OrderingError",
    "analyze_all_orderings",
    "analyze_event_ordering",
    "analyze_event_ordering_from_config",
    "detect_price_shocks",
    "detect_price_shocks_from_config",
    "save_orderings",
    "save_orderings_csv",
    "save_orderings_json",
]
