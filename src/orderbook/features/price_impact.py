"""
Price impact metrics (Kyle's Lambda).

Implements:
Kyle's Lambda (λ): λ = Cov(ΔP, Q) / Var(Q)

where:
- ΔP = price change (midpoint change)
- Q = signed order flow (positive for buy, negative for sell)

Kyle's lambda measures the price impact per unit of order flow.
Higher values indicate:
- Lower liquidity
- Greater market impact from trades
- Higher trading costs for large orders
"""

import polars as pl
import numpy as np


class PriceImpact:
    """Calculate price impact metrics including Kyle's Lambda."""
    
    @staticmethod
    def kyles_lambda(
        trades_df: pl.DataFrame,
        quotes_df: pl.DataFrame,
        window_size: int = 100,
    ) -> dict[str, float]:
        """
        Calculate Kyle's Lambda using regression.
        
        Formula: λ = Cov(ΔP, Q) / Var(Q)
        
        Interpretation:
        - λ represents the price impact coefficient
        - A trade of size Q moves the price by approximately λ × Q
        - Higher λ means lower liquidity and higher impact costs
        
        Args:
            trades_df: DataFrame with trades
            quotes_df: DataFrame with quotes
            window_size: Number of observations for regression (not used in simple version)
            
        Returns:
            Dictionary with lambda and related metrics
        """
        # Calculate signed volume: Q = +size for buy, -size for sell
        trades_with_flow = trades_df.with_columns([
            pl.when(pl.col("side") == "buy")
            .then(pl.col("size"))
            .otherwise(-pl.col("size"))
            .alias("signed_volume")
        ])
        
        # Join with quotes to get midpoint
        trades_with_quotes = trades_with_flow.join_asof(
            quotes_df.select([
                "timestamp",
                "symbol",
                ((pl.col("bid_price") + pl.col("ask_price")) / 2).alias("midpoint"),
            ]),
            on="timestamp",
            by="symbol",
            strategy="backward",
        )
        
        # Calculate price changes: ΔP = M_t - M_{t-1}
        data = trades_with_quotes.sort("timestamp").with_columns([
            pl.col("midpoint").diff().alias("price_change"),
        ])
        
        # Remove null values from diff
        data = data.filter(pl.col("price_change").is_not_null())
        
        # Calculate Kyle's Lambda: λ = Cov(ΔP, Q) / Var(Q)
        stats = data.select([
            pl.corr("price_change", "signed_volume").alias("correlation"),
            pl.col("price_change").std().alias("price_std"),
            pl.col("signed_volume").std().alias("volume_std"),
            pl.col("signed_volume").var().alias("volume_var"),
            pl.cov("price_change", "signed_volume").alias("covariance"),
        ])
        
        # Extract values
        row = stats.row(0, named=True)
        
        # λ = Cov(ΔP, Q) / Var(Q)
        kyles_lambda = row["covariance"] / row["volume_var"] if row["volume_var"] > 0 else 0.0
        
        # Price impact in basis points (for a standard size trade, e.g., 100 shares)
        standard_trade_size = 100.0
        price_impact_bps = abs(kyles_lambda * standard_trade_size) * 10000
        
        return {
            "kyles_lambda": kyles_lambda,
            "price_impact_bps": price_impact_bps,
            "correlation": row["correlation"],
            "covariance": row["covariance"],
            "volume_std": row["volume_std"],
        }
    
    @staticmethod
    def order_flow_imbalance(trades_df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate cumulative order flow imbalance.
        
        OFI = Σ(signed_volume)
        
        Args:
            trades_df: DataFrame with trades
            
        Returns:
            DataFrame with cumulative order flow
        """
        return trades_df.with_columns([
            pl.when(pl.col("side") == "buy")
            .then(pl.col("size"))
            .otherwise(-pl.col("size"))
            .alias("signed_volume")
        ]).with_columns([
            pl.col("signed_volume").cum_sum().alias("cumulative_ofi")
        ])
