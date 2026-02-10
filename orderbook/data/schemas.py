"""
Data schemas for market microstructure analysis.

Defines Pydantic models for trades, quotes, L2 orderbook data, and output metrics.
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Trade(BaseModel):
    """Individual trade execution."""
    
    timestamp: datetime
    symbol: str
    price: float = Field(gt=0, description="Trade price")
    size: float = Field(gt=0, description="Trade size/quantity")
    side: Literal["buy", "sell"]
    
    @field_validator("price", "size")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Must be positive")
        return v


class Quote(BaseModel):
    """Best bid/offer quote."""
    
    timestamp: datetime
    symbol: str
    bid_price: float = Field(gt=0)
    ask_price: float = Field(gt=0)
    bid_size: float = Field(gt=0)
    ask_size: float = Field(gt=0)
    
    @field_validator("ask_price")
    @classmethod
    def validate_spread(cls, v: float, info) -> float:
        if "bid_price" in info.data and v <= info.data["bid_price"]:
            raise ValueError("Ask price must be greater than bid price")
        return v


class L2OrderbookLevel(BaseModel):
    """Single level in L2 orderbook."""
    
    price: float = Field(gt=0)
    size: float = Field(gt=0)


class L2Orderbook(BaseModel):
    """Level 2 orderbook snapshot."""
    
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


class SpreadMetrics(BaseModel):
    """Spread-based liquidity metrics."""
    
    timestamp: datetime
    symbol: str
    quoted_spread: float = Field(description="Bid-ask spread")
    effective_spread: float = Field(description="Effective spread (2 * |price - midpoint|)")
    realized_spread: Optional[float] = Field(None, description="Realized spread")
    spread_bps: float = Field(description="Spread in basis points")


class PriceImpactMetrics(BaseModel):
    """Price impact and Kyle's Lambda metrics."""
    
    timestamp: datetime
    symbol: str
    kyles_lambda: float = Field(description="Kyle's lambda (price impact coefficient)")
    price_impact_bps: float = Field(description="Price impact in basis points")
    order_flow_imbalance: float = Field(description="Net order flow")


class VolatilityRegime(BaseModel):
    """Volatility regime classification."""
    
    timestamp: datetime
    symbol: str
    volatility: float = Field(ge=0, description="Estimated volatility")
    regime: Literal["low", "medium", "high"] = Field(description="Volatility regime")
    regime_change: bool = Field(False, description="Indicates regime transition")


class AnalysisResult(BaseModel):
    """Complete analysis output."""
    
    symbol: str
    start_time: datetime
    end_time: datetime
    num_trades: int
    num_quotes: int
    spread_metrics: list[SpreadMetrics]
    price_impact_metrics: list[PriceImpactMetrics]
    volatility_regimes: list[VolatilityRegime]
    avg_quoted_spread_bps: float
    avg_effective_spread_bps: float
    avg_kyles_lambda: float
