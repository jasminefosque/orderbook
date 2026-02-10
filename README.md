# Orderbook - Market Microstructure Analysis

Institutional-grade market structure analytics engine for liquidity monitoring, price discovery, and automated regulatory reporting in data-constrained environments.

## Overview

This project implements a comprehensive pipeline for transforming raw trade and quote data into institutional liquidity metrics. It uses a **"synthetic-first" strategy** to simulate Level 2 (L2) orderbook data, making it ideal for analysis under data constraints.

### Key Features

- **Liquidity Metrics**: Calculate Effective Spread, Realized Spread, and quoted bid-ask spreads
- **Price Impact Analysis**: Implement Kyle's Lambda for measuring price impact from order flow
- **Volatility Regime Detection**: Automatically classify market volatility into low/medium/high regimes
- **High Performance**: Built with Polars for fast DataFrame operations and Pydantic for validated schemas
- **Multiple Output Formats**: Export results as Parquet files and human-readable Markdown reports

## Installation

### Using pip

```bash
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Running the Example

```bash
python example.py
```

This will:
1. Generate synthetic market data (trades and quotes)
2. Calculate liquidity metrics
3. Detect volatility regimes
4. Output results to the `output/` directory:
   - `spread_metrics.parquet` - Spread-based liquidity metrics
   - `price_impact_metrics.parquet` - Kyle's Lambda and price impact
   - `volatility_regimes.parquet` - Volatility regime classifications
   - `analysis_report.md` - Human-readable analysis report

### Programmatic Usage

```python
from orderbook import run_analysis

# Run analysis with custom parameters
result = run_analysis(
    symbol="AAPL",
    duration_minutes=60,
    output_dir="output",
    seed=42,
)

# Access results
print(f"Average Effective Spread: {result.avg_effective_spread_bps:.2f} bps")
print(f"Kyle's Lambda: {result.avg_kyles_lambda:.6f}")
```

## Architecture

The pipeline consists of several modular components:

### Data Layer (`orderbook.data`)
- **Schemas**: Pydantic models for trades, quotes, L2 orderbook, and metrics
- **Synthetic Data Generator**: Generates realistic market data using geometric Brownian motion

### Metrics Layer (`orderbook.metrics`)
- **Spread Calculator**: Effective and realized spread calculations
- **Price Impact Calculator**: Kyle's Lambda implementation
- **Volatility Detector**: Regime detection based on rolling volatility

### Output Layer (`orderbook.output`)
- **Parquet Writer**: Efficient storage in columnar format
- **Markdown Reporter**: Human-readable analysis reports

### Pipeline (`orderbook.pipeline`)
- **Analysis Pipeline**: Orchestrates the complete workflow
- **run_analysis()**: Main entry point for end-to-end analysis

## Metrics Explained

### Effective Spread
Measures the actual cost of immediate execution:
```
Effective Spread = 2 × |trade_price - midpoint|
```

### Realized Spread
Separates execution cost from adverse selection:
```
Realized Spread = 2 × direction × (trade_price - midpoint_later)
```
where direction = +1 for buy, -1 for sell

### Kyle's Lambda
Measures price impact coefficient from order flow:
```
Kyle's Lambda = Cov(ΔPrice, SignedVolume) / Var(SignedVolume)
```

A higher lambda indicates greater price impact per unit of volume, suggesting lower market liquidity.

### Volatility Regimes
Based on rolling standard deviation of returns:
- **Low**: < 1% annualized volatility
- **Medium**: 1-3% annualized volatility
- **High**: > 3% annualized volatility

## Design Philosophy

### Analysis Under Data Constraints

This project is designed for scenarios where:
- Full L2 orderbook data is unavailable or expensive
- Historical data has gaps or quality issues
- Real-time infrastructure is limited

The synthetic-first approach allows:
- Testing and validation without real market data
- Consistent benchmarking across different periods
- Development and debugging in controlled environments

### Performance Focus

- **Polars** for vectorized DataFrame operations (faster than pandas)
- **Pydantic** for validated schemas and type safety
- **Parquet** for efficient columnar storage

## Project Structure

```
orderbook/
├── orderbook/
│   ├── __init__.py
│   ├── pipeline.py           # Main pipeline orchestrator
│   ├── data/
│   │   ├── schemas.py        # Pydantic data models
│   │   └── synthetic.py      # Synthetic data generator
│   ├── metrics/
│   │   ├── spreads.py        # Spread calculations
│   │   ├── price_impact.py   # Kyle's Lambda
│   │   └── volatility.py     # Regime detection
│   └── output/
│       ├── parquet_writer.py # Parquet output
│       └── markdown_report.py # Report generation
├── example.py                # Example usage
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## Requirements

- Python >= 3.9
- pydantic >= 2.0.0
- polars >= 0.19.0
- pyarrow >= 12.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0

## License

MIT License - See LICENSE file for details
