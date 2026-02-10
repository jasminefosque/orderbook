"""
Volatility estimation and regime detection.

Implements:
1. Realized Volatility: σ = √(Σ r_t²) where r_t = log(P_t / P_{t-1})
2. Regime Classification:
   - Low: σ < 1% (annualized)
   - Medium: 1% ≤ σ < 3% (annualized)
   - High: σ ≥ 3% (annualized)
"""

import polars as pl
import numpy as np


class VolatilityMetrics:
    """Calculate volatility and detect market regimes."""
    
    @staticmethod
    def realized_volatility(
        quotes_df: pl.DataFrame,
        window_size: int = 50,
        annualize: bool = True,
    ) -> pl.DataFrame:
        """
        Calculate realized volatility from quote data.
        
        Formula: σ = √(Σ r_t²) × scaling_factor
        
        where r_t = log(M_t / M_{t-1}) (log returns)
        
        For annualization with intraday data:
        - Assume N observations per day
        - Scaling factor = √(252 × N) for annual volatility
        
        Args:
            quotes_df: DataFrame with quotes
            window_size: Rolling window size
            annualize: Whether to annualize volatility (default True)
            
        Returns:
            DataFrame with volatility estimates
        """
        # Calculate midpoint
        data = quotes_df.sort("timestamp").with_columns([
            ((pl.col("bid_price") + pl.col("ask_price")) / 2).alias("midpoint"),
        ])
        
        # Calculate log returns: r_t = log(M_t / M_{t-1})
        data = data.with_columns([
            (pl.col("midpoint").log() - pl.col("midpoint").log().shift(1)).alias("log_returns"),
        ])
        
        # Calculate rolling standard deviation
        scaling_factor = np.sqrt(252) if annualize else 1.0
        
        data = data.with_columns([
            (pl.col("log_returns").rolling_std(window_size=window_size) * scaling_factor)
            .fill_null(0.0)
            .alias("volatility"),
        ])
        
        return data.select([
            "timestamp",
            "symbol",
            "midpoint",
            "log_returns",
            "volatility",
        ])
    
    @staticmethod
    def detect_regimes(
        volatility_df: pl.DataFrame,
        low_threshold: float = 0.01,
        high_threshold: float = 0.03,
    ) -> pl.DataFrame:
        """
        Classify volatility into market regimes.
        
        Regimes:
        - Low: σ < 1% (calm market, tight spreads expected)
        - Medium: 1% ≤ σ < 3% (normal market conditions)
        - High: σ ≥ 3% (stressed market, wide spreads, higher impact)
        
        Args:
            volatility_df: DataFrame with volatility column
            low_threshold: Threshold for low volatility (default 1%)
            high_threshold: Threshold for high volatility (default 3%)
            
        Returns:
            DataFrame with regime classifications
        """
        result = volatility_df.with_columns([
            pl.when(pl.col("volatility") < low_threshold)
            .then(pl.lit("low"))
            .when(pl.col("volatility") < high_threshold)
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
        
        return result.select([
            "timestamp",
            "symbol",
            "volatility",
            "regime",
            "regime_change",
        ])
    
    @staticmethod
    def calculate_with_regimes(
        quotes_df: pl.DataFrame,
        window_size: int = 50,
    ) -> pl.DataFrame:
        """
        Full pipeline: calculate volatility and detect regimes.
        
        Args:
            quotes_df: DataFrame with quotes
            window_size: Rolling window size
            
        Returns:
            DataFrame with volatility and regime information
        """
        vol_df = VolatilityMetrics.realized_volatility(quotes_df, window_size)
        regime_df = VolatilityMetrics.detect_regimes(vol_df)
        return regime_df
