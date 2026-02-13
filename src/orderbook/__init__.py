"""
Orderbook - Market Microstructure & Liquidity Lab

Institutional-grade analytics for liquidity monitoring and price discovery.
"""

__version__ = "0.1.0"

from orderbook.io import (
    Trade,
    Quote,
    SyntheticDataGenerator,
    AdvancedSyntheticGenerator,
    generate_market_data,
)
from orderbook.features import SpreadMetrics, PriceImpact, VolatilityMetrics

__all__ = [
    "__version__",
    "Trade",
    "Quote",
    "SyntheticDataGenerator",
    "AdvancedSyntheticGenerator",
    "generate_market_data",
    "SpreadMetrics",
    "PriceImpact",
    "VolatilityMetrics",
]
