# orderbook: Market Microstructure & Liquidity Lab

**Institutional Market Microstructure & Liquidity Analytics**

`orderbook` is a production-grade analytics suite designed for high-frequency market data analysis and regulatory monitoring. Built to address the challenges of "constrained data access," it provides a rigorous framework for simulating, cleaning, and analyzing liquidity dynamics across fragmented venues.

---

## Executive Summary

In institutional and regulatory environments (e.g., U.S. Treasury, MSRB), analyzing market health often requires working with restricted datasets or simulating impact before policy implementation. `orderbook` bridges this gap by providing:

* **High-Fidelity Simulation:** Deterministic synthetic trade-and-quote (TAQ) generation using geometric Brownian motion
* **Institutional Metrics:** Implementation of academic and industry-standard liquidity proxies
* **Policy Reporting:** Automated generation of market-impact memos and visualizations in Markdown and Parquet formats

This project is designed for:
- **Quantitative Researchers** validating market theories with reproducible synthetic data
- **Regulatory Analysts** monitoring liquidity across venues (Crypto, Fixed Income, Equities)
- **Portfolio Managers** assessing execution quality and market impact

---

## Core Analytical Engine

### 1. Liquidity & Spread Metrics

The lab implements precise measurements of execution costs and market friction:

#### **Effective Spread**
Measures the actual cost paid by a trader relative to the midpoint at the time of execution:

```
ES = 2 × |P_trade - M|
```

where `P_trade` is the execution price and `M` is the midpoint.

This metric captures both the quoted spread and any price improvement received.

#### **Realized Spread**
Captures the "true" cost to the liquidity provider by comparing the trade price to the midpoint `δ` seconds after the trade:

```
RS = 2 × D × (P_trade - M_t+δ)
```

where `D = +1` for buy orders, `D = -1` for sell orders.

**Interpretation:**
- `RS < ES` indicates adverse selection (informed trading)
- `RS ≈ ES` indicates uninformed trading (transient impact only)

### 2. Market Impact & Kyle's Lambda (λ)

Using a regression-based approach, the lab calculates **Kyle's Lambda**, representing the price move per unit of volume:

```
λ = Cov(ΔP, Q) / Var(Q)
```

where:
- `ΔP` = price change (midpoint change)
- `Q` = signed order flow (positive for buy, negative for sell)

**Interpretation:**
- A trade of size `Q` moves the price by approximately `λ × Q`
- Higher λ indicates greater price impact and lower market liquidity
- Critical metric for institutional desks determining market "capacity"

### 3. Volatility Regime Detection

A rolling-window classification system that categorizes market states using realized volatility:

```
σ = √(Σ r_t²) × √252
```

where `r_t = log(M_t / M_{t-1})` are log returns.

**Regime Classification:**
- **Low (Calm):** σ < 1% - Low spread, high depth, minimal price impact
- **Medium (Normal):** 1% ≤ σ < 3% - Standard market conditions
- **High (Stressed):** σ ≥ 3% - Widening spreads, liquidity evaporation, high price impact

---

## Why This Exists

In regulatory and institutional environments, access to high-fidelity L3 data is often restricted or expensive. `orderbook` provides a framework to:

* **Validate** market theories using deterministic synthetic data
* **Analyze** liquidity across venues with consistent methodology
* **Report** findings through automated, publishable-grade policy memos
* **Benchmark** execution quality without proprietary data dependencies

---

## Project Architecture

```text
orderbook/
├── src/orderbook/
│   ├── io/               # Pydantic schemas for TAQ data validation
│   │   ├── schemas.py    # Trade, Quote, L2Orderbook models
│   │   └── synthetic.py  # Synthetic L2 order book simulation
│   ├── features/         # Quantitative logic (spreads, lambda, regimes)
│   │   ├── spreads.py    # Effective/Realized spread calculations
│   │   ├── price_impact.py  # Kyle's Lambda implementation
│   │   └── volatility.py    # Regime detection
│   ├── cli/              # Command-line interface
│   │   └── main.py       # build/report commands
│   └── output/           # Report generation engines
│       ├── parquet_writer.py   # Efficient columnar storage
│       └── markdown_report.py  # Human-readable reports
├── tests/                # Unit tests for mathematical accuracy
├── outputs/              # Parquet logs and Markdown reports (gitignored)
├── pyproject.toml        # Dependency and build management
├── LICENSE               # MIT License
└── README.md             # This file
```

---

## Getting Started

### Installation

```bash
git clone https://github.com/jasminefosque/orderbook.git
cd orderbook
pip install -e .
```

### Quick Start

Run the full analytical pipeline in **synthetic mode** to generate a demo report:

```bash
# Generate data and compute metrics
python -m orderbook.cli build --mode synthetic

# Compile the Market Monitoring Report
python -m orderbook.cli report
```

This will:
1. Generate synthetic market data (trades and quotes) using GBM
2. Calculate liquidity metrics (spreads, Kyle's Lambda)
3. Detect volatility regimes
4. Output results to `outputs/`:
   - `spread_metrics.parquet` - Spread-based liquidity metrics
   - `price_impact_metrics.parquet` - Kyle's Lambda and order flow
   - `volatility_regimes.parquet` - Regime classifications
   - `analysis_report.md` - Human-readable market health report

### Programmatic Usage

```python
from orderbook.io import SyntheticDataGenerator
from orderbook.features import SpreadMetrics, PriceImpact, VolatilityMetrics
import polars as pl

# Generate synthetic data
gen = SyntheticDataGenerator(symbol="AAPL", seed=42)
trades, quotes = gen.generate_market_session(duration_minutes=60)

# Convert to DataFrames
trades_df = pl.DataFrame([t.model_dump() for t in trades])
quotes_df = pl.DataFrame([q.model_dump() for q in quotes])

# Calculate metrics
spread_df = SpreadMetrics.effective_spread(trades_df, quotes_df)
lambda_result = PriceImpact.kyles_lambda(trades_df, quotes_df)
volatility_df = VolatilityMetrics.calculate_with_regimes(quotes_df)

print(f"Kyle's Lambda: {lambda_result['kyles_lambda']:.6f}")
```

---

## Data Strategy

To remain compliant with institutional data privacy, `orderbook` supports three ingestion modes:

1. **Synthetic:** Deterministic simulation based on geometric Brownian motion (GBM)
2. **CSV/Parquet Import:** Secure ingestion of local files following the `Trade`/`Quote` schema
3. **Live API (Future):** Direct ingestion of public APIs (Binance, Coinbase) for live demonstrations

All data files are excluded from version control via `.gitignore` to maintain privacy.

---

## Methodology & References

This project implements methodologies from seminal papers in market microstructure:

* **Kyle (1985):** "Continuous Auctions and Insider Trading" - Lambda calculation
* **Hasbrouck (2007):** "Empirical Market Microstructure" - Spread decomposition
* **Amihud (2002):** "Illiquidity and Stock Returns" - Liquidity measurement
* **Harris (2003):** "Trading and Exchanges" - Market design fundamentals

---

## Technical Stack

- **Python:** 3.10+ (type hints, match statements)
- **Polars:** High-performance DataFrame operations (faster than pandas)
- **Pydantic:** Data validation and schema enforcement
- **Click:** CLI framework for build/report workflow
- **PyArrow:** Efficient Parquet I/O

---

## Resume Pitch

When linking this on your CV, describe it as:

> **orderbook (Open Source):** Developed a modular microstructure laboratory to simulate and analyze market liquidity. Built to demonstrate policy-impact modeling and price discovery analysis for fragmented markets (Fixed Income/Digital Assets) under data-access constraints. Implements Kyle's Lambda, spread decomposition, and volatility regime detection using Polars and Pydantic.

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

---

## Contact

**Jasmine Fosque** - [GitHub](https://github.com/jasminefosque)

For questions about institutional deployment or custom analytics, please open an issue.
