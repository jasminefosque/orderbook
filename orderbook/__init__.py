"""
Orderbook - Market Microstructure Analysis Pipeline

An institutional-grade market structure analytics engine for liquidity monitoring,
price discovery, and automated regulatory reporting in data-constrained environments.
"""

__version__ = "0.1.0"

from orderbook.pipeline import run_analysis

__all__ = ["run_analysis", "__version__"]
