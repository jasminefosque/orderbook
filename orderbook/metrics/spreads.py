"""
Spread metrics calculator.

Implements Effective Spread and Realized Spread calculations for liquidity analysis.
"""

from datetime import timedelta
import polars as pl

from orderbook.data.schemas import Trade, Quote, SpreadMetrics


class SpreadCalculator:
    """Calculate various spread metrics for liquidity analysis."""
    
    def __init__(self, lookback_seconds: float = 300.0):
        """
        Initialize spread calculator.
        
        Args:
            lookback_seconds: Time window for realized spread calculation
        """
        self.lookback_seconds = lookback_seconds
    
    def calculate_quoted_spread(self, quote: Quote) -> float:
        """
        Calculate quoted (bid-ask) spread.
        
        Args:
            quote: Quote data
            
        Returns:
            Quoted spread
        """
        return quote.ask_price - quote.bid_price
    
    def calculate_effective_spread(self, trade: Trade, quote: Quote) -> float:
        """
        Calculate effective spread.
        
        Effective spread = 2 * |trade_price - midpoint|
        
        Args:
            trade: Trade execution
            quote: Corresponding quote
            
        Returns:
            Effective spread
        """
        midpoint = (quote.bid_price + quote.ask_price) / 2
        return 2 * abs(trade.price - midpoint)
    
    def calculate_realized_spread(
        self,
        trade: Trade,
        quote_at_trade: Quote,
        quote_later: Quote,
    ) -> float:
        """
        Calculate realized spread.
        
        Realized spread = 2 * D * (trade_price - midpoint_later)
        where D = +1 for buy, -1 for sell
        
        Args:
            trade: Trade execution
            quote_at_trade: Quote at trade time
            quote_later: Quote at later time
            
        Returns:
            Realized spread
        """
        direction = 1 if trade.side == "buy" else -1
        midpoint_later = (quote_later.bid_price + quote_later.ask_price) / 2
        return 2 * direction * (trade.price - midpoint_later)
    
    def calculate_metrics_polars(
        self,
        trades_df: pl.DataFrame,
        quotes_df: pl.DataFrame,
    ) -> pl.DataFrame:
        """
        Calculate spread metrics using Polars for performance.
        
        Args:
            trades_df: DataFrame with columns: timestamp, symbol, price, size, side
            quotes_df: DataFrame with columns: timestamp, symbol, bid_price, ask_price
            
        Returns:
            DataFrame with spread metrics
        """
        # Ensure sorted by timestamp
        trades_df = trades_df.sort("timestamp")
        quotes_df = quotes_df.sort("timestamp")
        
        # Join trades with nearest quotes (asof join)
        trades_with_quotes = trades_df.join_asof(
            quotes_df,
            on="timestamp",
            by="symbol",
            strategy="backward",
            suffix="_quote",
        )
        
        # Calculate midpoint and spreads
        result = trades_with_quotes.with_columns([
            ((pl.col("bid_price") + pl.col("ask_price")) / 2).alias("midpoint"),
            (pl.col("ask_price") - pl.col("bid_price")).alias("quoted_spread"),
        ]).with_columns([
            (2 * (pl.col("price") - pl.col("midpoint")).abs()).alias("effective_spread"),
            ((pl.col("quoted_spread") / pl.col("midpoint")) * 10000).alias("spread_bps"),
        ])
        
        return result.select([
            "timestamp",
            "symbol",
            "quoted_spread",
            "effective_spread",
            "spread_bps",
        ])
    
    def to_pydantic_models(self, df: pl.DataFrame) -> list[SpreadMetrics]:
        """
        Convert Polars DataFrame to Pydantic models.
        
        Args:
            df: DataFrame with spread metrics
            
        Returns:
            List of SpreadMetrics
        """
        metrics = []
        for row in df.iter_rows(named=True):
            metrics.append(SpreadMetrics(
                timestamp=row["timestamp"],
                symbol=row["symbol"],
                quoted_spread=row["quoted_spread"],
                effective_spread=row["effective_spread"],
                realized_spread=None,  # Calculated separately
                spread_bps=row["spread_bps"],
            ))
        return metrics
