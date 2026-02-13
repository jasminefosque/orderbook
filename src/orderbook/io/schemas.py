"""
Data schemas for orderbook analysis.

Defines Pydantic models for Trade and Quote objects to ensure data integrity
during ingestion from CSV or synthetic generators.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Trade(BaseModel):
    """
    Individual trade execution.
    
    Represents a single market transaction with timestamp, price, size, and direction.
    """
    
    timestamp: datetime = Field(description="Trade execution time")
    symbol: str = Field(description="Trading symbol/ticker")
    price: float = Field(gt=0, description="Execution price")
    size: float = Field(gt=0, description="Trade size/quantity")
    side: Literal["buy", "sell"] = Field(description="Trade direction")
    
    @field_validator("price", "size")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price and size must be positive")
        return v


class Quote(BaseModel):
    """
    Best bid/offer (BBO) quote.
    
    Represents the top of the orderbook with best bid and ask prices and sizes.
    """
    
    timestamp: datetime = Field(description="Quote timestamp")
    symbol: str = Field(description="Trading symbol/ticker")
    bid_price: float = Field(gt=0, description="Best bid price")
    ask_price: float = Field(gt=0, description="Best ask price")
    bid_size: float = Field(gt=0, description="Size available at bid")
    ask_size: float = Field(gt=0, description="Size available at ask")
    
    @field_validator("ask_price")
    @classmethod
    def validate_spread(cls, v: float, info) -> float:
        """Ensure ask price is greater than bid price."""
        if "bid_price" in info.data and v <= info.data["bid_price"]:
            raise ValueError("Ask price must be greater than bid price")
        return v
    
    @property
    def midpoint(self) -> float:
        """Calculate midpoint price."""
        return (self.bid_price + self.ask_price) / 2
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        return self.ask_price - self.bid_price


class L2OrderbookLevel(BaseModel):
    """Single level in L2 orderbook."""
    
    price: float = Field(gt=0)
    size: float = Field(gt=0)


class L2Orderbook(BaseModel):
    """
    Level 2 orderbook snapshot.
    
    Contains multiple price levels on both bid and ask sides.
    """
    
    timestamp: datetime
    symbol: str
    bids: list[L2OrderbookLevel] = Field(description="Sorted descending by price")
    asks: list[L2OrderbookLevel] = Field(description="Sorted ascending by price")
    
    @field_validator("bids", "asks")
    @classmethod
    def validate_non_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Must have at least one level")
        return v
