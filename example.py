#!/usr/bin/env python3
"""
Example script demonstrating the orderbook analysis pipeline.

This script generates synthetic market data and runs the complete analysis pipeline,
producing Parquet files and a Markdown report.
"""

from orderbook import run_analysis


def main():
    """Run example analysis."""
    print("=" * 80)
    print("Market Microstructure Analysis Pipeline - Example Run")
    print("=" * 80)
    print()
    
    # Run analysis with default parameters
    result = run_analysis(
        symbol="AAPL",
        duration_minutes=60,
        output_dir="output",
        seed=42,
    )
    
    print()
    print("=" * 80)
    print("Analysis complete! Check the 'output' directory for results.")
    print("=" * 80)
    print()
    print("Output files:")
    print("  - output/spread_metrics.parquet")
    print("  - output/price_impact_metrics.parquet")
    print("  - output/volatility_regimes.parquet")
    print("  - output/analysis_report.md")
    print()
    print("Volatility Regime Summary:")
    regime_counts = {"low": 0, "medium": 0, "high": 0}
    for regime in result.volatility_regimes:
        regime_counts[regime.regime] += 1
    
    total = len(result.volatility_regimes)
    if total > 0:
        print(f"  Low:    {regime_counts['low']:3d} ({regime_counts['low']/total*100:5.1f}%)")
        print(f"  Medium: {regime_counts['medium']:3d} ({regime_counts['medium']/total*100:5.1f}%)")
        print(f"  High:   {regime_counts['high']:3d} ({regime_counts['high']/total*100:5.1f}%)")


if __name__ == "__main__":
    main()
