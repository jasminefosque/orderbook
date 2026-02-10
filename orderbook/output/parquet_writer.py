"""
Parquet output writer.

Writes analysis results to Parquet format for efficient storage and downstream processing.
"""

from pathlib import Path
import polars as pl

from orderbook.data.schemas import AnalysisResult


class ParquetWriter:
    """Write analysis results to Parquet files."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize Parquet writer.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_spread_metrics(self, df: pl.DataFrame, filename: str = "spread_metrics.parquet"):
        """
        Write spread metrics to Parquet.
        
        Args:
            df: DataFrame with spread metrics
            filename: Output filename
        """
        output_path = self.output_dir / filename
        df.write_parquet(output_path)
        return output_path
    
    def write_price_impact_metrics(
        self,
        df: pl.DataFrame,
        filename: str = "price_impact_metrics.parquet",
    ):
        """
        Write price impact metrics to Parquet.
        
        Args:
            df: DataFrame with price impact metrics
            filename: Output filename
        """
        output_path = self.output_dir / filename
        df.write_parquet(output_path)
        return output_path
    
    def write_volatility_regimes(
        self,
        df: pl.DataFrame,
        filename: str = "volatility_regimes.parquet",
    ):
        """
        Write volatility regimes to Parquet.
        
        Args:
            df: DataFrame with volatility regimes
            filename: Output filename
        """
        output_path = self.output_dir / filename
        df.write_parquet(output_path)
        return output_path
    
    def write_all(
        self,
        spread_df: pl.DataFrame,
        impact_df: pl.DataFrame,
        volatility_df: pl.DataFrame,
    ) -> dict[str, Path]:
        """
        Write all metrics to Parquet files.
        
        Args:
            spread_df: Spread metrics
            impact_df: Price impact metrics
            volatility_df: Volatility regimes
            
        Returns:
            Dictionary mapping metric types to file paths
        """
        paths = {
            "spread_metrics": self.write_spread_metrics(spread_df),
            "price_impact_metrics": self.write_price_impact_metrics(impact_df),
            "volatility_regimes": self.write_volatility_regimes(volatility_df),
        }
        return paths
