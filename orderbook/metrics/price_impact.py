"""
Price impact calculator (Kyle's Lambda).

Implements Kyle's Lambda as a measure of price impact from order flow.
"""

import polars as pl
import numpy as np

from orderbook.data.schemas import PriceImpactMetrics


class PriceImpactCalculator:
    """Calculate price impact metrics including Kyle's Lambda."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize price impact calculator.
        
        Args:
            window_size: Rolling window size for regression
        """
        self.window_size = window_size
    
    def calculate_order_flow_imbalance(self, trades_df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate order flow imbalance (net signed volume).
        
        Args:
            trades_df: DataFrame with trades
            
        Returns:
            DataFrame with order flow imbalance
        """
        return trades_df.with_columns([
            pl.when(pl.col("side") == "buy")
            .then(pl.col("size"))
            .otherwise(-pl.col("size"))
            .alias("signed_volume")
        ])
    
    def calculate_kyles_lambda_polars(
        self,
        trades_df: pl.DataFrame,
        quotes_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """
        Calculate Kyle's Lambda using rolling regression.
        
        Kyle's Lambda = Cov(ΔP, V) / Var(V)
        where ΔP is price change and V is signed volume
        
        Args:
            trades_df: DataFrame with trades
            quotes_df: DataFrame with quotes
            
        Returns:
            DataFrame with price impact metrics
        """
        # Add signed volume
        trades_with_flow = self.calculate_order_flow_imbalance(trades_df)
        
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
        
        # Calculate price changes
        data = trades_with_quotes.with_columns([
            pl.col("midpoint").diff().alias("price_change"),
        ])
        
        # For simplicity, calculate lambda over entire dataset
        # In production, use rolling window
        stats = data.select([
            pl.col("symbol").first(),
            pl.col("timestamp").first(),
            pl.corr("price_change", "signed_volume").alias("correlation"),
            pl.col("price_change").std().alias("price_std"),
            pl.col("signed_volume").std().alias("volume_std"),
            pl.col("signed_volume").mean().alias("avg_order_flow"),
        ]).with_columns([
            (pl.col("correlation") * pl.col("price_std") / pl.col("volume_std"))
            .fill_null(0.0)
            .alias("kyles_lambda"),
        ])
        
        # Calculate price impact in basis points
        result = stats.with_columns([
            ((pl.col("kyles_lambda") * 100.0) * 10000).alias("price_impact_bps"),
        ])
        
        return result.select([
            "timestamp",
            "symbol",
            "kyles_lambda",
            "price_impact_bps",
            "avg_order_flow",
        ])
    
    def to_pydantic_models(self, df: pl.DataFrame) -> list[PriceImpactMetrics]:
        """
        Convert Polars DataFrame to Pydantic models.
        
        Args:
            df: DataFrame with price impact metrics
            
        Returns:
            List of PriceImpactMetrics
        """
        metrics = []
        for row in df.iter_rows(named=True):
            metrics.append(PriceImpactMetrics(
                timestamp=row["timestamp"],
                symbol=row["symbol"],
                kyles_lambda=float(row["kyles_lambda"]),
                price_impact_bps=float(row["price_impact_bps"]),
                order_flow_imbalance=float(row["avg_order_flow"]),
            ))
        return metrics
