"""
Volatility regime detection.

Implements volatility estimation and regime classification for market analysis.
"""

import polars as pl
import numpy as np

from orderbook.data.schemas import VolatilityRegime


class VolatilityRegimeDetector:
    """Detect volatility regimes from market data."""
    
    def __init__(
        self,
        window_size: int = 50,
        low_threshold: float = 0.01,
        high_threshold: float = 0.03,
    ):
        """
        Initialize volatility regime detector.
        
        Args:
            window_size: Rolling window for volatility calculation
            low_threshold: Threshold for low volatility regime
            high_threshold: Threshold for high volatility regime
        """
        self.window_size = window_size
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
    
    def calculate_realized_volatility(
        self,
        quotes_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """
        Calculate realized volatility from quote data.
        
        Uses midpoint returns in a rolling window.
        
        Args:
            quotes_df: DataFrame with quotes
            
        Returns:
            DataFrame with volatility estimates
        """
        # Calculate midpoint
        data = quotes_df.with_columns([
            ((pl.col("bid_price") + pl.col("ask_price")) / 2).alias("midpoint"),
        ])
        
        # Calculate returns
        data = data.with_columns([
            (pl.col("midpoint").pct_change()).alias("returns"),
        ])
        
        # Calculate rolling volatility (annualized)
        # Note: For intraday data, adjust scaling factor based on sampling frequency
        data = data.with_columns([
            (pl.col("returns").rolling_std(window_size=self.window_size) * np.sqrt(252))
            .fill_null(0.0)
            .alias("volatility"),
        ])
        
        return data.select([
            "timestamp",
            "symbol",
            "volatility",
        ])
    
    def classify_regime(self, volatility_df: pl.DataFrame) -> pl.DataFrame:
        """
        Classify volatility into regimes.
        
        Args:
            volatility_df: DataFrame with volatility estimates
            
        Returns:
            DataFrame with regime classifications
        """
        result = volatility_df.with_columns([
            pl.when(pl.col("volatility") < self.low_threshold)
            .then(pl.lit("low"))
            .when(pl.col("volatility") < self.high_threshold)
            .then(pl.lit("medium"))
            .otherwise(pl.lit("high"))
            .alias("regime")
        ])
        
        # Detect regime changes
        result = result.with_columns([
            (pl.col("regime") != pl.col("regime").shift(1))
            .fill_null(False)
            .alias("regime_change")
        ])
        
        return result
    
    def detect_regimes_polars(
        self,
        quotes_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """
        Full volatility regime detection pipeline.
        
        Args:
            quotes_df: DataFrame with quotes
            
        Returns:
            DataFrame with volatility regimes
        """
        vol_df = self.calculate_realized_volatility(quotes_df)
        regime_df = self.classify_regime(vol_df)
        return regime_df
    
    def to_pydantic_models(self, df: pl.DataFrame) -> list[VolatilityRegime]:
        """
        Convert Polars DataFrame to Pydantic models.
        
        Args:
            df: DataFrame with volatility regimes
            
        Returns:
            List of VolatilityRegime
        """
        regimes = []
        for row in df.iter_rows(named=True):
            regimes.append(VolatilityRegime(
                timestamp=row["timestamp"],
                symbol=row["symbol"],
                volatility=float(row["volatility"]),
                regime=row["regime"],
                regime_change=bool(row["regime_change"]),
            ))
        return regimes
