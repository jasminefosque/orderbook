"""
Command-line interface for orderbook analytics.

Provides two main commands:
1. build --mode synthetic: Generate data and compute metrics
2. report: Generate Markdown reports from computed metrics
"""

import click
from pathlib import Path
from datetime import datetime

from orderbook.io import Trade, Quote, AdvancedSyntheticGenerator, generate_market_data
from orderbook.features import SpreadMetrics, PriceImpact, VolatilityMetrics
import polars as pl


def trades_to_polars(trades: list[Trade]) -> pl.DataFrame:
    """Convert list of Trade objects to Polars DataFrame."""
    return pl.DataFrame([t.model_dump() for t in trades])


def quotes_to_polars(quotes: list[Quote]) -> pl.DataFrame:
    """Convert list of Quote objects to Polars DataFrame."""
    return pl.DataFrame([q.model_dump() for q in quotes])


@click.group()
@click.version_option(version="0.1.0", prog_name="orderbook")
def cli():
    """
    orderbook - Market Microstructure & Liquidity Analytics
    
    Institutional-grade analytics for liquidity monitoring and price discovery.
    """
    pass


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["synthetic"], case_sensitive=False),
    default="synthetic",
    help="Data generation mode (currently only synthetic supported)",
)
@click.option(
    "--symbol",
    default="AAPL",
    help="Trading symbol",
)
@click.option(
    "--duration",
    default=60,
    type=int,
    help="Duration in minutes for synthetic session",
)
@click.option(
    "--output-dir",
    default="outputs",
    type=click.Path(),
    help="Output directory for results",
)
@click.option(
    "--seed",
    default=42,
    type=int,
    help="Random seed for reproducibility",
)
def build(mode: str, symbol: str, duration: int, output_dir: str, seed: int):
    """
    Generate data and compute microstructure metrics.
    
    Example:
        python -m orderbook.cli build --mode synthetic --duration 120
    """
    click.echo("=" * 80)
    click.echo("orderbook - Build Pipeline")
    click.echo("=" * 80)
    click.echo()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic data
    click.echo(f"Generating synthetic market data for {symbol}...")
    click.echo(f"  Duration: {duration} minutes")
    click.echo(f"  Random seed: {seed}")
    click.echo()
    
    # Use advanced generator for more realistic data
    generator = AdvancedSyntheticGenerator(
        symbol=symbol,
        initial_price=150.0,
        base_spread_bps=2.0,
        seed=seed,
    )
    
    trades, quotes = generator.generate_session(
        duration_minutes=duration,
        observations_per_minute=10,
    )
    
    click.echo(f"✓ Generated {len(trades)} trades and {len(quotes)} quotes")
    click.echo()
    
    # Convert to Polars DataFrames
    trades_df = trades_to_polars(trades)
    quotes_df = quotes_to_polars(quotes)
    
    # Calculate metrics
    click.echo("Computing liquidity metrics...")
    
    # 1. Spread metrics
    click.echo("  - Calculating Effective Spreads...")
    spread_df = SpreadMetrics.effective_spread(trades_df, quotes_df)
    spread_path = output_path / "spread_metrics.parquet"
    spread_df.write_parquet(spread_path)
    click.echo(f"    ✓ Saved to {spread_path}")
    
    # 2. Price impact (Kyle's Lambda)
    click.echo("  - Calculating Kyle's Lambda...")
    lambda_result = PriceImpact.kyles_lambda(trades_df, quotes_df)
    
    # Save as single-row DataFrame
    lambda_df = pl.DataFrame({
        "timestamp": [datetime.now()],
        "symbol": [symbol],
        "kyles_lambda": [lambda_result["kyles_lambda"]],
        "price_impact_bps": [lambda_result["price_impact_bps"]],
        "correlation": [lambda_result["correlation"]],
        "covariance": [lambda_result["covariance"]],
        "volume_std": [lambda_result["volume_std"]],
    })
    lambda_path = output_path / "price_impact_metrics.parquet"
    lambda_df.write_parquet(lambda_path)
    click.echo(f"    ✓ Saved to {lambda_path}")
    
    # 3. Volatility regimes
    click.echo("  - Detecting volatility regimes...")
    volatility_df = VolatilityMetrics.calculate_with_regimes(quotes_df, window_size=50)
    vol_path = output_path / "volatility_regimes.parquet"
    volatility_df.write_parquet(vol_path)
    click.echo(f"    ✓ Saved to {vol_path}")
    
    click.echo()
    click.echo("=" * 80)
    click.echo("Build Complete")
    click.echo("=" * 80)
    click.echo()
    click.echo("Summary Statistics:")
    click.echo(f"  Average Quoted Spread:    {spread_df['quoted_spread_bps'].mean():.2f} bps")
    click.echo(f"  Average Effective Spread: {spread_df['effective_spread_bps'].mean():.2f} bps")
    click.echo(f"  Kyle's Lambda:            {lambda_result['kyles_lambda']:.6f}")
    click.echo(f"  Price Impact (100 shares): {lambda_result['price_impact_bps']:.4f} bps")
    click.echo()
    
    # Regime summary
    regime_counts = volatility_df.group_by("regime").len()
    total_regimes = len(volatility_df)
    click.echo("Volatility Regimes:")
    for row in regime_counts.iter_rows(named=True):
        pct = (row["len"] / total_regimes * 100) if total_regimes > 0 else 0
        click.echo(f"  {row['regime'].capitalize():8s}: {row['len']:4d} ({pct:5.1f}%)")
    
    click.echo()
    click.echo(f"Next: Run 'python -m orderbook.cli report' to generate analysis report")


@cli.command()
@click.option(
    "--output-dir",
    default="outputs",
    type=click.Path(exists=True),
    help="Directory containing metric files",
)
def report(output_dir: str):
    """
    Generate Markdown analysis report from computed metrics.
    
    Example:
        python -m orderbook.cli report --output-dir outputs
    """
    click.echo("=" * 80)
    click.echo("orderbook - Report Generator")
    click.echo("=" * 80)
    click.echo()
    
    output_path = Path(output_dir)
    
    # Load metric files
    click.echo("Loading computed metrics...")
    
    try:
        spread_df = pl.read_parquet(output_path / "spread_metrics.parquet")
        lambda_df = pl.read_parquet(output_path / "price_impact_metrics.parquet")
        volatility_df = pl.read_parquet(output_path / "volatility_regimes.parquet")
        click.echo("✓ All metric files loaded successfully")
        click.echo()
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Run 'python -m orderbook.cli build' first to generate metrics", err=True)
        return
    
    # Generate report
    click.echo("Generating Market Microstructure Analysis Report...")
    
    # Extract key statistics
    symbol = lambda_df["symbol"][0]
    start_time = spread_df["timestamp"].min()
    end_time = spread_df["timestamp"].max()
    duration_minutes = (end_time - start_time).total_seconds() / 60
    
    avg_quoted_spread = spread_df["quoted_spread_bps"].mean()
    avg_effective_spread = spread_df["effective_spread_bps"].mean()
    kyles_lambda = lambda_df["kyles_lambda"][0]
    price_impact = lambda_df["price_impact_bps"][0]
    
    # Regime statistics
    regime_counts = volatility_df.group_by("regime").len()
    total_regimes = len(volatility_df)
    regime_changes = volatility_df["regime_change"].sum()
    
    # Generate Markdown report
    report_content = f"""# Market Microstructure Analysis Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

**Symbol:** {symbol}  
**Analysis Period:** {start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Duration:** {duration_minutes:.1f} minutes

### Data Overview
- **Total Observations:** {len(spread_df):,} trades analyzed
- **Quote Updates:** {len(volatility_df):,} quote snapshots

---

## Liquidity Metrics

### Spread Analysis

The bid-ask spread is a key indicator of market liquidity. Lower spreads indicate higher liquidity and more efficient markets.

- **Average Quoted Spread:** {avg_quoted_spread:.2f} bps
- **Average Effective Spread:** {avg_effective_spread:.2f} bps
- **Effective/Quoted Ratio:** {(avg_effective_spread / avg_quoted_spread * 100) if avg_quoted_spread > 0 else 0:.1f}%

**Interpretation:**
The effective spread represents the actual cost of immediate execution, accounting for price improvement.
- A ratio close to 100% suggests limited price improvement
- Lower ratios indicate better execution quality and competitive market making

---

## Price Impact Analysis

### Kyle's Lambda (λ)

Kyle's Lambda measures the price impact per unit of order flow. It represents the market's liquidity depth and the cost of trading large orders.

- **Kyle's Lambda:** {kyles_lambda:.6f}
- **Price Impact (100 shares):** {price_impact:.4f} bps

**Interpretation:**
- A trade of 100 shares would move the price by approximately {price_impact:.4f} basis points
- This metric is crucial for:
  - Optimal execution strategies
  - Market impact estimation
  - Trading cost analysis for institutional orders

**Formula:** λ = Cov(ΔP, Q) / Var(Q)
- Where ΔP is the price change and Q is signed order flow

---

## Volatility Regime Analysis

### Regime Distribution

Volatility regimes help identify periods of market stress and adjust risk management accordingly.
"""

    # Add regime statistics
    for row in regime_counts.iter_rows(named=True):
        pct = (row["len"] / total_regimes * 100) if total_regimes > 0 else 0
        report_content += f"\n- **{row['regime'].capitalize()} Volatility:** {row['len']} periods ({pct:.1f}%)"
    
    report_content += f"""
- **Regime Changes:** {regime_changes} transitions detected

### Implications

- **High volatility periods** require wider spreads and more conservative position sizing
- **Low volatility periods** present opportunities for tighter spreads and higher leverage
- **Frequent regime changes** suggest unstable market conditions requiring adaptive strategies

---

## Methodology Notes

### Data Generation

This analysis uses **synthetic L2 orderbook data** generated via geometric Brownian motion (GBM), designed for "analysis under data constraints" scenarios where proprietary data is unavailable.

### Metrics Definitions

**Effective Spread:** `ES = 2 × |P_trade - M|`
- Measures actual execution cost relative to midpoint
- Captures both quoted spread and price improvement

**Realized Spread:** `RS = 2 × D × (P_trade - M_t+δ)`
- Separates execution cost from adverse selection
- D = +1 for buy, -1 for sell

**Kyle's Lambda:** `λ = Cov(ΔP, Q) / Var(Q)`
- Measures price impact coefficient from order flow
- Critical for institutional trading cost analysis

**Volatility Regime:** Rolling standard deviation of returns with thresholds:
- Low: σ < 1% annualized
- Medium: 1% ≤ σ < 3% annualized
- High: σ ≥ 3% annualized

---

## References

- Kyle, A. S. (1985). "Continuous Auctions and Insider Trading." *Econometrica*, 53(6), 1315-1335.
- Hasbrouck, J. (2007). *Empirical Market Microstructure: The Institutions, Economics, and Econometrics of Securities Trading*. Oxford University Press.
- Amihud, Y. (2002). "Illiquidity and Stock Returns: Cross-Section and Time-Series Effects." *Journal of Financial Markets*, 5(1), 31-56.

---

*Report generated by orderbook v0.1.0*  
*For questions or institutional deployment, visit: https://github.com/jasminefosque/orderbook*
"""
    
    # Write report
    report_path = output_path / "analysis_report.md"
    report_path.write_text(report_content)
    
    click.echo(f"✓ Report saved to: {report_path}")
    click.echo()
    click.echo("=" * 80)
    click.echo("Report Generation Complete")
    click.echo("=" * 80)
    click.echo()
    click.echo(f"View your report: {report_path}")


if __name__ == "__main__":
    cli()
