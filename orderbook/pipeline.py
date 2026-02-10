"""
Market microstructure analysis pipeline.

Orchestrates the complete analysis workflow from data generation to output.
"""

from pathlib import Path
from typing import Optional
import polars as pl

from orderbook.data.schemas import Trade, Quote, AnalysisResult
from orderbook.data.synthetic import SyntheticDataGenerator
from orderbook.metrics.spreads import SpreadCalculator
from orderbook.metrics.price_impact import PriceImpactCalculator
from orderbook.metrics.volatility import VolatilityRegimeDetector
from orderbook.output.parquet_writer import ParquetWriter
from orderbook.output.markdown_report import MarkdownReportGenerator


def trades_to_polars(trades: list[Trade]) -> pl.DataFrame:
    """Convert list of Trade objects to Polars DataFrame."""
    return pl.DataFrame([
        {
            "timestamp": t.timestamp,
            "symbol": t.symbol,
            "price": t.price,
            "size": t.size,
            "side": t.side,
        }
        for t in trades
    ])


def quotes_to_polars(quotes: list[Quote]) -> pl.DataFrame:
    """Convert list of Quote objects to Polars DataFrame."""
    return pl.DataFrame([
        {
            "timestamp": q.timestamp,
            "symbol": q.symbol,
            "bid_price": q.bid_price,
            "ask_price": q.ask_price,
            "bid_size": q.bid_size,
            "ask_size": q.ask_size,
        }
        for q in quotes
    ])


class AnalysisPipeline:
    """Complete market microstructure analysis pipeline."""
    
    def __init__(
        self,
        output_dir: str = "output",
        spread_lookback_seconds: float = 300.0,
        volatility_window: int = 50,
    ):
        """
        Initialize analysis pipeline.
        
        Args:
            output_dir: Directory for output files
            spread_lookback_seconds: Lookback window for realized spread
            volatility_window: Window size for volatility calculation
        """
        self.output_dir = Path(output_dir)
        self.spread_calc = SpreadCalculator(lookback_seconds=spread_lookback_seconds)
        self.impact_calc = PriceImpactCalculator(window_size=100)
        self.volatility_detector = VolatilityRegimeDetector(window_size=volatility_window)
        self.parquet_writer = ParquetWriter(self.output_dir)
        self.report_generator = MarkdownReportGenerator(self.output_dir)
    
    def run(
        self,
        trades: list[Trade],
        quotes: list[Quote],
        generate_report: bool = True,
    ) -> AnalysisResult:
        """
        Run complete analysis pipeline.
        
        Args:
            trades: List of trade executions
            quotes: List of quote updates
            generate_report: Whether to generate Markdown report
            
        Returns:
            Complete analysis results
        """
        # Convert to Polars DataFrames for performance
        trades_df = trades_to_polars(trades)
        quotes_df = quotes_to_polars(quotes)
        
        # Calculate metrics
        spread_df = self.spread_calc.calculate_metrics_polars(trades_df, quotes_df)
        impact_df = self.impact_calc.calculate_kyles_lambda_polars(trades_df, quotes_df)
        volatility_df = self.volatility_detector.detect_regimes_polars(quotes_df)
        
        # Write to Parquet
        parquet_paths = self.parquet_writer.write_all(spread_df, impact_df, volatility_df)
        
        # Convert to Pydantic models
        spread_metrics = self.spread_calc.to_pydantic_models(spread_df)
        impact_metrics = self.impact_calc.to_pydantic_models(impact_df)
        volatility_regimes = self.volatility_detector.to_pydantic_models(volatility_df)
        
        # Calculate summary statistics
        avg_quoted_spread_bps = spread_df["spread_bps"].mean() if len(spread_df) > 0 else 0.0
        avg_effective_spread_bps = (
            (spread_df["effective_spread"] / (spread_df["quoted_spread"] + 1e-10) * avg_quoted_spread_bps).mean()
            if len(spread_df) > 0 else 0.0
        )
        avg_kyles_lambda = impact_df["kyles_lambda"].mean() if len(impact_df) > 0 else 0.0
        
        # Create result object
        result = AnalysisResult(
            symbol=trades[0].symbol if trades else "UNKNOWN",
            start_time=trades[0].timestamp if trades else quotes[0].timestamp,
            end_time=trades[-1].timestamp if trades else quotes[-1].timestamp,
            num_trades=len(trades),
            num_quotes=len(quotes),
            spread_metrics=spread_metrics,
            price_impact_metrics=impact_metrics,
            volatility_regimes=volatility_regimes,
            avg_quoted_spread_bps=float(avg_quoted_spread_bps),
            avg_effective_spread_bps=float(avg_effective_spread_bps),
            avg_kyles_lambda=float(avg_kyles_lambda),
        )
        
        # Generate Markdown report
        if generate_report:
            report_path = self.report_generator.generate_report(result)
            print(f"Generated report: {report_path}")
        
        # Print summary
        print(f"\nAnalysis complete:")
        print(f"  - Spread metrics written to: {parquet_paths['spread_metrics']}")
        print(f"  - Price impact metrics written to: {parquet_paths['price_impact_metrics']}")
        print(f"  - Volatility regimes written to: {parquet_paths['volatility_regimes']}")
        
        return result


def run_analysis(
    symbol: str = "AAPL",
    duration_minutes: int = 60,
    output_dir: str = "output",
    seed: Optional[int] = 42,
) -> AnalysisResult:
    """
    Run market microstructure analysis with synthetic data.
    
    This is the main entry point for the orderbook analysis pipeline.
    
    Args:
        symbol: Trading symbol
        duration_minutes: Duration of synthetic session
        output_dir: Output directory for results
        seed: Random seed for reproducibility
        
    Returns:
        Analysis results
    """
    print(f"Generating synthetic market data for {symbol}...")
    
    # Generate synthetic data
    generator = SyntheticDataGenerator(
        symbol=symbol,
        initial_price=150.0,
        volatility=0.02,
        spread_bps=5.0,
        seed=seed,
    )
    
    trades, quotes = generator.generate_market_session(
        duration_minutes=duration_minutes,
        trades_per_minute=10,
        quotes_per_minute=20,
    )
    
    print(f"Generated {len(trades)} trades and {len(quotes)} quotes")
    
    # Run pipeline
    pipeline = AnalysisPipeline(output_dir=output_dir)
    result = pipeline.run(trades, quotes, generate_report=True)
    
    print("\nSummary Statistics:")
    print(f"  Average Quoted Spread: {result.avg_quoted_spread_bps:.2f} bps")
    print(f"  Average Effective Spread: {result.avg_effective_spread_bps:.2f} bps")
    print(f"  Average Kyle's Lambda: {result.avg_kyles_lambda:.6f}")
    
    return result
