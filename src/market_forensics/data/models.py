"""Canonical data models for market forensics pipeline.

These schemas define the expected structure for all market data flowing through
the pipeline. Loaders must convert raw data into these types.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Side(Enum):
    """Trade side: buy or sell."""

    BUY = "buy"
    SELL = "sell"


class EventDirection(Enum):
    """Direction of a detected event."""

    UP = "up"
    DOWN = "down"


@dataclass(frozen=True)
class Trade:
    """A single trade execution.

    Attributes:
        timestamp: UTC timestamp of the trade.
        symbol: Trading pair symbol (e.g., 'BTC-USDT').
        price: Execution price.
        size: Trade size in base currency.
        side: Buy or sell side.
        trade_id: Optional unique identifier for the trade.
    """

    timestamp: datetime
    symbol: str
    price: float
    size: float
    side: Side
    trade_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate trade data."""
        if self.price <= 0:
            raise ValueError(f"Trade price must be positive, got {self.price}")
        if self.size <= 0:
            raise ValueError(f"Trade size must be positive, got {self.size}")


@dataclass(frozen=True)
class TopOfBook:
    """Top of book (best bid/ask) snapshot.

    Attributes:
        timestamp: UTC timestamp of the snapshot.
        symbol: Trading pair symbol (e.g., 'BTC-USDT').
        bid_price: Best bid price.
        bid_size: Size available at best bid.
        ask_price: Best ask price.
        ask_size: Size available at best ask.
    """

    timestamp: datetime
    symbol: str
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float

    def __post_init__(self) -> None:
        """Validate top of book data."""
        if self.bid_price <= 0:
            raise ValueError(f"Bid price must be positive, got {self.bid_price}")
        if self.ask_price <= 0:
            raise ValueError(f"Ask price must be positive, got {self.ask_price}")
        if self.bid_size < 0:
            raise ValueError(f"Bid size must be non-negative, got {self.bid_size}")
        if self.ask_size < 0:
            raise ValueError(f"Ask size must be non-negative, got {self.ask_size}")
        if self.bid_price > self.ask_price:
            raise ValueError(
                f"Bid price ({self.bid_price}) cannot exceed ask price ({self.ask_price})"
            )

    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        return (self.bid_price + self.ask_price) / 2

    @property
    def spread(self) -> float:
        """Calculate absolute spread."""
        return self.ask_price - self.bid_price

    @property
    def spread_bps(self) -> float:
        """Calculate spread in basis points relative to mid price."""
        return (self.spread / self.mid_price) * 10000


@dataclass(frozen=True)
class Event:
    """A detected market event (e.g., price shock).

    Attributes:
        timestamp: UTC timestamp when the event was detected.
        symbol: Trading pair symbol.
        event_type: Type of event (e.g., 'price_shock').
        direction: Direction of the event (up or down).
        magnitude: Size of the move (e.g., percentage change).
        metadata: Optional additional event-specific data.
    """

    timestamp: datetime
    symbol: str
    event_type: str
    direction: EventDirection
    magnitude: float
    metadata: Optional[dict] = None
