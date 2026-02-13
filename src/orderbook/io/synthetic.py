"""
Synthetic data generator for constrained data environments.

Generates realistic trade/quote sequences using geometric Brownian motion
for testing and development.
"""

from datetime import datetime, timedelta
from typing import Optional
import numpy as np

from orderbook.io.schemas import Trade, Quote, L2Orderbook, L2OrderbookLevel


class SyntheticDataGenerator:
    """
    Generate deterministic synthetic market data.
    
    Uses geometric Brownian motion (GBM) to create realistic price paths,
    then generates trades and quotes around those prices.
    """
    
    def __init__(
        self,
        symbol: str = "AAPL",
        initial_price: float = 150.0,
        volatility: float = 0.02,
        spread_bps: float = 5.0,
        seed: Optional[int] = None,
    ):
        """
        Initialize synthetic data generator.
        
        Args:
            symbol: Trading symbol
            initial_price: Starting price
            volatility: Daily volatility (annualized)
            spread_bps: Typical bid-ask spread in basis points
            seed: Random seed for deterministic generation
        """
        self.symbol = symbol
        self.initial_price = initial_price
        self.volatility = volatility
        self.spread_bps = spread_bps
        self.rng = np.random.default_rng(seed)
        
        # State tracking
        self.current_price = initial_price
        self.current_time = datetime(2024, 1, 1, 9, 30, 0)
    
    def generate_price_path(self, num_steps: int, dt_seconds: float = 1.0) -> np.ndarray:
        """
        Generate synthetic price path using geometric Brownian motion.
        
        dS = μ * S * dt + σ * S * dW
        
        Args:
            num_steps: Number of price updates
            dt_seconds: Time step in seconds
            
        Returns:
            Array of prices
        """
        dt = dt_seconds / (252 * 24 * 3600)  # Convert to years for GBM
        sqrt_dt = np.sqrt(dt)
        
        # Geometric Brownian Motion
        drift = -0.5 * self.volatility**2 * dt
        diffusion = self.volatility * sqrt_dt * self.rng.standard_normal(num_steps)
        log_returns = drift + diffusion
        
        prices = self.initial_price * np.exp(np.cumsum(log_returns))
        return prices
    
    def generate_l2_snapshot(self, midprice: float, num_levels: int = 5) -> L2Orderbook:
        """
        Generate synthetic L2 orderbook snapshot.
        
        Args:
            midprice: Current mid price
            num_levels: Number of price levels on each side
            
        Returns:
            L2Orderbook snapshot
        """
        # Calculate half spread
        half_spread = midprice * (self.spread_bps / 10000) / 2
        
        bids = []
        asks = []
        
        for i in range(num_levels):
            # Price levels with increasing spread
            level_spread = half_spread * (1 + i * 0.5)
            bid_price = midprice - level_spread
            ask_price = midprice + level_spread
            
            # Size decreases with distance from mid
            base_size = 100.0
            size = base_size * self.rng.exponential(1.0) * (1 / (1 + i))
            
            bids.append(L2OrderbookLevel(price=bid_price, size=size))
            asks.append(L2OrderbookLevel(price=ask_price, size=size))
        
        return L2Orderbook(
            timestamp=self.current_time,
            symbol=self.symbol,
            bids=bids,
            asks=asks,
        )
    
    def generate_quote(self, midprice: float) -> Quote:
        """
        Generate synthetic quote from L2 snapshot.
        
        Args:
            midprice: Current mid price
            
        Returns:
            Quote with best bid/offer
        """
        l2 = self.generate_l2_snapshot(midprice, num_levels=1)
        
        return Quote(
            timestamp=self.current_time,
            symbol=self.symbol,
            bid_price=l2.bids[0].price,
            ask_price=l2.asks[0].price,
            bid_size=l2.bids[0].size,
            ask_size=l2.asks[0].size,
        )
    
    def generate_trade(self, midprice: float) -> Trade:
        """
        Generate synthetic trade.
        
        Args:
            midprice: Current mid price
            
        Returns:
            Trade execution
        """
        # Random trade direction
        side = "buy" if self.rng.random() > 0.5 else "sell"
        
        # Trade price with some noise around mid
        price_noise = midprice * (self.spread_bps / 10000) * self.rng.uniform(-1, 1)
        price = midprice + price_noise
        
        # Trade size
        size = 50.0 * self.rng.exponential(1.0)
        
        return Trade(
            timestamp=self.current_time,
            symbol=self.symbol,
            price=price,
            size=size,
            side=side,
        )
    
    def generate_market_session(
        self,
        duration_minutes: int = 60,
        trades_per_minute: int = 10,
        quotes_per_minute: int = 20,
    ) -> tuple[list[Trade], list[Quote]]:
        """
        Generate a full market session with trades and quotes.
        
        Args:
            duration_minutes: Session duration in minutes
            trades_per_minute: Average trade frequency
            quotes_per_minute: Average quote update frequency
            
        Returns:
            Tuple of (trades, quotes)
        """
        num_trades = duration_minutes * trades_per_minute
        num_quotes = duration_minutes * quotes_per_minute
        
        # Generate price path
        total_steps = max(num_trades, num_quotes)
        prices = self.generate_price_path(
            total_steps, 
            dt_seconds=60.0 / max(trades_per_minute, quotes_per_minute)
        )
        
        trades = []
        quotes = []
        
        # Generate trades
        trade_times = np.sort(self.rng.uniform(0, duration_minutes * 60, num_trades))
        for i, t in enumerate(trade_times):
            self.current_time = datetime(2024, 1, 1, 9, 30, 0) + timedelta(seconds=t)
            price_idx = min(int(i * len(prices) / num_trades), len(prices) - 1)
            trades.append(self.generate_trade(prices[price_idx]))
        
        # Generate quotes
        quote_times = np.sort(self.rng.uniform(0, duration_minutes * 60, num_quotes))
        for i, t in enumerate(quote_times):
            self.current_time = datetime(2024, 1, 1, 9, 30, 0) + timedelta(seconds=t)
            price_idx = min(int(i * len(prices) / num_quotes), len(prices) - 1)
            quotes.append(self.generate_quote(prices[price_idx]))
        
        return trades, quotes
