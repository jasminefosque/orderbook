# Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/jasminefosque/orderbook.git
cd orderbook

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Basic Usage

### 1. Generate Synthetic Data and Compute Metrics

```bash
# Run with default parameters (60 minutes, AAPL)
python -m orderbook.cli.main build --mode synthetic

# Customize duration and symbol
python -m orderbook.cli.main build --mode synthetic --symbol TSLA --duration 120 --seed 42
```

This command will:
- Generate synthetic trade and quote data
- Calculate effective spreads
- Compute Kyle's Lambda (price impact)
- Detect volatility regimes
- Save results as Parquet files in `outputs/`

### 2. Generate Analysis Report

```bash
python -m orderbook.cli.main report --output-dir outputs
```

This will create `outputs/analysis_report.md` with:
- Executive summary
- Liquidity metrics analysis
- Price impact interpretation
- Volatility regime distribution
- Methodology notes

## Programmatic Usage

```python
from orderbook import AdvancedSyntheticGenerator, generate_market_data
from orderbook.features import SpreadMetrics, PriceImpact, VolatilityMetrics
import polars as pl

# Option 1: Quick DataFrame generation
df = generate_market_data(n_rows=5000, seed=42)
print(df.head())

# Option 2: Full session with Trade/Quote objects
generator = AdvancedSyntheticGenerator(symbol="AAPL", seed=42)
trades, quotes = generator.generate_session(duration_minutes=60)

# Convert to DataFrames for analysis
trades_df = pl.DataFrame([t.model_dump() for t in trades])
quotes_df = pl.DataFrame([q.model_dump() for q in quotes])

# Calculate metrics
spread_df = SpreadMetrics.effective_spread(trades_df, quotes_df)
lambda_result = PriceImpact.kyles_lambda(trades_df, quotes_df)
volatility_df = VolatilityMetrics.calculate_with_regimes(quotes_df)

print(f"Kyle's Lambda: {lambda_result['kyles_lambda']:.6f}")
print(f"Price Impact (100 shares): {lambda_result['price_impact_bps']:.4f} bps")
```

## Output Files

After running the build command, you'll find:

- `outputs/spread_metrics.parquet` - Effective/quoted spreads for each trade
- `outputs/price_impact_metrics.parquet` - Kyle's Lambda and related metrics
- `outputs/volatility_regimes.parquet` - Volatility regime classifications over time
- `outputs/analysis_report.md` - Human-readable analysis report

## Example Analysis Report Excerpt

```markdown
## Executive Summary

**Symbol:** AAPL  
**Analysis Period:** 2024-01-01 09:30:00 to 2024-01-01 10:30:00  
**Duration:** 60.0 minutes

### Liquidity Metrics
- **Average Quoted Spread:** 79.25 bps
- **Average Effective Spread:** 79.25 bps
- **Kyle's Lambda:** 0.000008
- **Price Impact (100 shares):** 8.4844 bps
```

## Advanced Features

### Custom Volatility Thresholds

```python
from orderbook.features import VolatilityMetrics

# Customize regime thresholds
volatility_df = VolatilityMetrics.realized_volatility(quotes_df, window_size=100)
regimes = VolatilityMetrics.detect_regimes(
    volatility_df,
    low_threshold=0.005,  # 0.5% for low
    high_threshold=0.04,  # 4% for high
)
```

### Generate Sample Data File

```bash
# Run the generator standalone to create a sample Parquet file
python -m orderbook.io.generator
# Creates: data/sample/synthetic_market.parquet
```

## Understanding the Metrics

### Effective Spread
- **Formula:** `ES = 2 × |P_trade - M|`
- **Interpretation:** Actual cost of immediate execution
- **Use Case:** Measure execution quality and liquidity

### Kyle's Lambda
- **Formula:** `λ = Cov(ΔP, Q) / Var(Q)`
- **Interpretation:** Price impact per unit of order flow
- **Use Case:** Estimate market impact for large orders

### Volatility Regimes
- **Low:** σ < 1% (tight spreads, high liquidity)
- **Medium:** 1% ≤ σ < 3% (normal market)
- **High:** σ ≥ 3% (wide spreads, stress conditions)

## Troubleshooting

### Module not found error
```bash
# Ensure package is installed
pip install -e .

# Check installation
python -c "import orderbook; print(orderbook.__version__)"
```

### No output files generated
```bash
# Ensure you ran build first
python -m orderbook.cli.main build --mode synthetic

# Then generate report
python -m orderbook.cli.main report
```

## Next Steps

1. **Customize parameters** - Adjust duration, seed, and symbol
2. **Export to CSV** - Use Polars to convert Parquet files: `df.write_csv()`
3. **Visualize results** - Plot spread time series or regime transitions
4. **Extend metrics** - Add your own microstructure calculations to `features/`

## Citation

If you use this in research or publications:

```
Fosque, J. (2024). orderbook: Market Microstructure & Liquidity Lab.
GitHub repository: https://github.com/jasminefosque/orderbook
```

## Support

For issues or questions:
- Open an issue on GitHub
- Review the comprehensive docstrings in the source code
- Check the README.md for methodology details
