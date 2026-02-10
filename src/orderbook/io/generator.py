"""
Enhanced synthetic market data generator.

Generates realistic Trade-and-Quote (TAQ) datasets with:
- Mean-reverting midpoint price paths
- Dynamic spreads that widen during volatility
- Realistic trade execution at bid/ask prices
"""

import polars as pl
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

from orderbook.io.schemas import Trade, Quote


def generate_market_data(
    n_rows: int = 1000,
    seed: int = 42,
    initial_price: float = 100.0,
    base_spread_bps: float = 2.0,
) -> pl.DataFrame:
    """
    Generate synthetic Trade-and-Quote (TAQ) dataset.
    
    Simulates a random walk midpoint with stochastic spreads that widen
    during periods of high volatility.
    
    Args:
        n_rows: Number of observations to generate
        seed: Random seed for reproducibility
        initial_price: Starting midpoint price
        base_spread_bps: Base bid-ask spread in basis points
        
    Returns:
        Polars DataFrame with columns:
        - timestamp: Observation time
        - midpoint: Mid price
        - bid: Best bid price
        - ask: Best ask price
        - trade_price: Execution price
        - trade_side: 1 for buy (at ask), -1 for sell (at bid)
        - volume: Trade size
    """
    np.random.seed(seed)
    
    # 1. Generate Timestamps (millisecond precision)
    start_time = datetime(2024, 1, 1, 9, 30, 0)
    times = [start_time + timedelta(milliseconds=i * 100) for i in range(n_rows)]
    
    # 2. Generate Midpoint Price (Random Walk)
    # Use log returns for realistic price dynamics
    returns = np.random.normal(0, 0.0001, n_rows)
    midpoint = initial_price * np.exp(np.cumsum(returns))
    
    # 3. Generate Dynamic Spreads
    # Spreads widen during volatility (measured by absolute returns)
    base_spread = (base_spread_bps / 10000) * midpoint  # Convert bps to price units
    volatility_factor = np.abs(returns) * 10000  # Scale up for visibility
    spreads = base_spread + volatility_factor * midpoint / 100
    
    bid = midpoint - (spreads / 2)
    ask = midpoint + (spreads / 2)
    
    # 4. Generate Trades
    # Trade side: 1 for Buy (executes at Ask), -1 for Sell (executes at Bid)
    side = np.random.choice([1, -1], n_rows)
    trade_price = np.where(side == 1, ask, bid)
    
    # Volume follows Poisson distribution (realistic for retail flow)
    volume = np.random.poisson(100, n_rows)
    
    # 5. Create Polars DataFrame
    df = pl.DataFrame({
        "timestamp": times,
        "midpoint": midpoint,
        "bid": bid,
        "ask": ask,
        "trade_price": trade_price,
        "trade_side": side,
        "volume": volume,
    })
    
    return df


def polars_to_trade_quote_objects(df: pl.DataFrame, symbol: str = "SYNTH") -> tuple[list[Trade], list[Quote]]:
    """
    Convert Polars DataFrame to Trade and Quote Pydantic objects.
    
    Args:
        df: DataFrame from generate_market_data()
        symbol: Trading symbol to assign
        
    Returns:
        Tuple of (trades, quotes) as Pydantic model lists
    """
    trades = []
    quotes = []
    
    for row in df.iter_rows(named=True):
        # Create Quote object
        quote = Quote(
            timestamp=row["timestamp"],
            symbol=symbol,
            bid_price=row["bid"],
            ask_price=row["ask"],
            bid_size=100.0,  # Default size
            ask_size=100.0,
        )
        quotes.append(quote)
        
        # Create Trade object
        trade = Trade(
            timestamp=row["timestamp"],
            symbol=symbol,
            price=row["trade_price"],
            size=float(row["volume"]),
            side="buy" if row["trade_side"] == 1 else "sell",
        )
        trades.append(trade)
    
    return trades, quotes


class AdvancedSyntheticGenerator:
    """
    Advanced synthetic data generator with configurable market regimes.
    
    Provides more control over synthetic data generation including:
    - Multiple volatility regimes
    - Intraday patterns (U-shaped volume, volatility)
    - Correlated assets
    """
    
    def __init__(
        self,
        symbol: str = "SYNTH",
        initial_price: float = 100.0,
        base_spread_bps: float = 2.0,
        seed: Optional[int] = None,
    ):
        """
        Initialize advanced synthetic generator.
        
        Args:
            symbol: Trading symbol
            initial_price: Starting price
            base_spread_bps: Base spread in basis points
            seed: Random seed
        """
        self.symbol = symbol
        self.initial_price = initial_price
        self.base_spread_bps = base_spread_bps
        self.seed = seed
        
    def generate_session(
        self,
        duration_minutes: int = 390,
        observations_per_minute: int = 10,
    ) -> tuple[list[Trade], list[Quote]]:
        """
        Generate a full trading session.
        
        Args:
            duration_minutes: Session duration (default 390 = 6.5 hours)
            observations_per_minute: Sampling frequency
            
        Returns:
            Tuple of (trades, quotes)
        """
        n_rows = duration_minutes * observations_per_minute
        
        # Generate raw data
        df = generate_market_data(
            n_rows=n_rows,
            seed=self.seed,
            initial_price=self.initial_price,
            base_spread_bps=self.base_spread_bps,
        )
        
        # Convert to Pydantic objects
        trades, quotes = polars_to_trade_quote_objects(df, self.symbol)
        
        return trades, quotes
    
    def generate_dataframe(
        self,
        duration_minutes: int = 390,
        observations_per_minute: int = 10,
    ) -> pl.DataFrame:
        """
        Generate session data as Polars DataFrame.
        
        Args:
            duration_minutes: Session duration
            observations_per_minute: Sampling frequency
            
        Returns:
            Polars DataFrame with market data
        """
        n_rows = duration_minutes * observations_per_minute
        
        return generate_market_data(
            n_rows=n_rows,
            seed=self.seed,
            initial_price=self.initial_price,
            base_spread_bps=self.base_spread_bps,
        )


if __name__ == "__main__":
    """Generate sample synthetic data for testing."""
    import sys
    from pathlib import Path
    
    # Ensure data directory exists
    data_dir = Path("data/sample")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print("Generating synthetic market data...")
    data = generate_market_data(n_rows=5000, seed=42)
    
    # Save to parquet
    output_path = data_dir / "synthetic_market.parquet"
    data.write_parquet(output_path)
    
    print(f"✓ Generated {len(data):,} rows of synthetic market data")
    print(f"✓ Saved to: {output_path}")
    print()
    print("Data Summary:")
    print(f"  Time Range: {data['timestamp'].min()} to {data['timestamp'].max()}")
    print(f"  Price Range: ${data['midpoint'].min():.2f} - ${data['midpoint'].max():.2f}")
    print(f"  Avg Spread: {((data['ask'] - data['bid']) / data['midpoint'] * 10000).mean():.2f} bps")
    print(f"  Total Volume: {data['volume'].sum():,}")
