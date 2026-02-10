"""
Markdown report generator.

Creates human-readable analysis reports in Markdown format.
"""

from pathlib import Path
from datetime import datetime
import polars as pl

from orderbook.data.schemas import AnalysisResult


class MarkdownReportGenerator:
    """Generate Markdown analysis reports."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_summary_section(self, result: AnalysisResult) -> str:
        """Generate executive summary section."""
        return f"""## Executive Summary

**Symbol:** {result.symbol}  
**Analysis Period:** {result.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {result.end_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Duration:** {(result.end_time - result.start_time).total_seconds() / 60:.1f} minutes

### Data Overview
- **Total Trades:** {result.num_trades:,}
- **Total Quotes:** {result.num_quotes:,}
- **Trade Frequency:** {result.num_trades / ((result.end_time - result.start_time).total_seconds() / 60):.1f} trades/minute
- **Quote Frequency:** {result.num_quotes / ((result.end_time - result.start_time).total_seconds() / 60):.1f} quotes/minute

"""
    
    def generate_spread_section(self, result: AnalysisResult) -> str:
        """Generate spread analysis section."""
        return f"""## Liquidity Metrics

### Spread Analysis
The bid-ask spread is a key indicator of market liquidity. Lower spreads indicate higher liquidity.

- **Average Quoted Spread:** {result.avg_quoted_spread_bps:.2f} bps
- **Average Effective Spread:** {result.avg_effective_spread_bps:.2f} bps
- **Effective/Quoted Ratio:** {result.avg_effective_spread_bps / result.avg_quoted_spread_bps * 100 if result.avg_quoted_spread_bps > 0 else 0:.1f}%

The effective spread represents the actual cost of immediate execution, accounting for price improvement.
A ratio close to 100% suggests limited price improvement; lower ratios indicate better execution quality.

"""
    
    def generate_price_impact_section(self, result: AnalysisResult) -> str:
        """Generate price impact analysis section."""
        return f"""## Price Impact Analysis

### Kyle's Lambda
Kyle's Lambda measures the price impact per unit of order flow. Higher values indicate lower liquidity
and greater price impact from trades.

- **Average Kyle's Lambda:** {result.avg_kyles_lambda:.6f}
- **Interpretation:** A trade of 100 shares would move the price by approximately {abs(result.avg_kyles_lambda * 100):.4f} dollars

This metric is crucial for:
- Optimal execution strategies
- Market impact estimation
- Trading cost analysis

"""
    
    def generate_volatility_section(self, result: AnalysisResult) -> str:
        """Generate volatility regime section."""
        if not result.volatility_regimes:
            return ""
        
        # Count regime occurrences
        regime_counts = {"low": 0, "medium": 0, "high": 0}
        regime_changes = 0
        
        for regime in result.volatility_regimes:
            regime_counts[regime.regime] += 1
            if regime.regime_change:
                regime_changes += 1
        
        total = len(result.volatility_regimes)
        
        return f"""## Volatility Regime Analysis

### Regime Distribution
Volatility regimes help identify periods of market stress and adjust risk management accordingly.

- **Low Volatility:** {regime_counts['low']} periods ({regime_counts['low']/total*100:.1f}%)
- **Medium Volatility:** {regime_counts['medium']} periods ({regime_counts['medium']/total*100:.1f}%)
- **High Volatility:** {regime_counts['high']} periods ({regime_counts['high']/total*100:.1f}%)
- **Regime Changes:** {regime_changes}

### Implications
- High volatility periods require wider spreads and more conservative position sizing
- Low volatility periods present opportunities for tighter spreads and higher leverage
- Frequent regime changes suggest unstable market conditions

"""
    
    def generate_footer(self) -> str:
        """Generate report footer."""
        return f"""---

## Methodology Notes

### Data Generation
This analysis uses synthetic L2 orderbook data generated via geometric Brownian motion,
designed for "analysis under data constraints" scenarios.

### Metrics Definitions

**Effective Spread:** `2 × |trade_price - midpoint|`
- Measures actual execution cost relative to midpoint

**Realized Spread:** `2 × direction × (trade_price - midpoint_later)`
- Separates execution cost from adverse selection

**Kyle's Lambda:** `Cov(ΔPrice, SignedVolume) / Var(SignedVolume)`
- Measures price impact coefficient from order flow

**Volatility Regime:** Rolling standard deviation of returns with thresholds:
- Low: < 1% annualized
- Medium: 1-3% annualized  
- High: > 3% annualized

---

*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def generate_report(
        self,
        result: AnalysisResult,
        filename: str = "analysis_report.md",
    ) -> Path:
        """
        Generate complete Markdown report.
        
        Args:
            result: Analysis results
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        report = f"""# Market Microstructure Analysis Report

{self.generate_summary_section(result)}
{self.generate_spread_section(result)}
{self.generate_price_impact_section(result)}
{self.generate_volatility_section(result)}
{self.generate_footer()}
"""
        
        output_path = self.output_dir / filename
        output_path.write_text(report)
        return output_path
