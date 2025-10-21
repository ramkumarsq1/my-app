"""
Market Data Module
Handles all market data operations for Nifty:
- Real-time spot price fetching
- ATM strike calculation (dynamic based on current price)
- Index data retrieval
- Market status checking
- Trading hours validation
"""

import sys
from pathlib import Path
from datetime import datetime, time as dt_time
from typing import Dict, Optional, Tuple
import pytz

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import (
    TRADING_SYMBOL, EXCHANGE, STRIKE_INTERVAL,
    TRADING_START_TIME, TRADING_END_TIME, TIMEZONE,
    MARKET_OPEN_TIME, MARKET_CLOSE_TIME
)
from src.utils.logger import get_logger
from src.api.kite_wrapper import KiteWrapper


class MarketData:
    """
    Market Data Manager
    Provides real-time market data with emphasis on dynamic calculations
    """

    def __init__(self, kite_wrapper: KiteWrapper):
        """
        Initialize Market Data Manager

        Args:
            kite_wrapper: Initialized KiteWrapper instance
        """
        self.kite = kite_wrapper
        self.logger = get_logger(__name__)

        # Cache for reducing API calls
        self._cache = {}
        self._cache_timeout = 1  # seconds

        # Timezone
        self.tz = pytz.timezone(TIMEZONE)

        self.logger.info("MarketData initialized")

    # =========================================================================
    # SPOT PRICE METHODS
    # =========================================================================

    def get_nifty_spot_price(self, use_cache: bool = True) -> float:
        """
        Get current Nifty 50 spot price (DYNAMIC)

        Args:
            use_cache: Use cached value if available and recent

        Returns:
            Current Nifty spot price

        Example:
            >>> spot = market_data.get_nifty_spot_price()
            >>> print(f"Nifty: {spot}")
            24150.75
        """
        try:
            cache_key = 'nifty_spot'

            # Check cache
            if use_cache and cache_key in self._cache:
                cached_time, cached_value = self._cache[cache_key]
                if (datetime.now() - cached_time).total_seconds() < self._cache_timeout:
                    return cached_value

            # Fetch from API
            # Note: Use "NSE:NIFTY 50" for spot price
            quote = self.kite.get_ltp(["NSE:NIFTY 50"])
            spot_price = quote.get("NSE:NIFTY 50", {}).get("last_price", 0)

            if spot_price == 0:
                self.logger.error("Failed to fetch Nifty spot price")
                raise ValueError("Could not fetch Nifty spot price")

            # Update cache
            self._cache[cache_key] = (datetime.now(), spot_price)

            self.logger.debug(f"Nifty Spot: {spot_price}")
            return spot_price

        except Exception as e:
            self.logger.error(f"Error fetching Nifty spot price: {e}")
            raise

    def get_nifty_ohlc(self) -> Dict:
        """
        Get Nifty OHLC data for today

        Returns:
            Dictionary with open, high, low, close, last_price
        """
        try:
            ohlc = self.kite.get_ohlc(["NSE:NIFTY 50"])
            data = ohlc.get("NSE:NIFTY 50", {}).get("ohlc", {})

            self.logger.debug(f"Nifty OHLC: O={data.get('open')} H={data.get('high')} L={data.get('low')}")
            return data

        except Exception as e:
            self.logger.error(f"Error fetching Nifty OHLC: {e}")
            raise

    def get_index_quote(self, symbol: str = "NIFTY 50") -> Dict:
        """
        Get detailed quote for index

        Args:
            symbol: Index symbol (NIFTY 50, NIFTY BANK, etc.)

        Returns:
            Detailed quote dictionary
        """
        try:
            quote = self.kite.get_quote([f"NSE:{symbol}"])
            return quote.get(f"NSE:{symbol}", {})

        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {e}")
            raise

    # =========================================================================
    # ATM STRIKE CALCULATION (DYNAMIC)
    # =========================================================================

    def calculate_atm_strike(self, spot_price: float = None, strike_interval: int = None) -> int:
        """
        Calculate At-The-Money strike price (DYNAMIC)
        Rounds to nearest strike based on strike interval

        Args:
            spot_price: Current spot price (fetches if not provided)
            strike_interval: Strike interval (default from config)

        Returns:
            ATM strike price

        Example:
            >>> # If Nifty spot is 24,137.50 and strike interval is 50
            >>> atm = market_data.calculate_atm_strike()
            >>> print(atm)
            24150
        """
        try:
            if spot_price is None:
                spot_price = self.get_nifty_spot_price()

            if strike_interval is None:
                strike_interval = STRIKE_INTERVAL

            # Round to nearest strike
            atm_strike = round(spot_price / strike_interval) * strike_interval

            self.logger.debug(f"ATM Strike: {atm_strike} (Spot: {spot_price})")
            return int(atm_strike)

        except Exception as e:
            self.logger.error(f"Error calculating ATM strike: {e}")
            raise

    def get_strikes_around_atm(self, num_strikes: int = 5, spot_price: float = None) -> Tuple[list, int]:
        """
        Get strike prices around ATM (DYNAMIC)

        Args:
            num_strikes: Number of strikes on each side of ATM
            spot_price: Current spot price (fetches if not provided)

        Returns:
            Tuple of (list of strikes, atm_strike)

        Example:
            >>> strikes, atm = market_data.get_strikes_around_atm(num_strikes=3)
            >>> print(strikes)
            [24050, 24100, 24150, 24200, 24250, 24300, 24350]
            >>> print(f"ATM: {atm}")
            24150
        """
        try:
            atm_strike = self.calculate_atm_strike(spot_price)

            # Generate strikes
            strikes = []
            for i in range(-num_strikes, num_strikes + 1):
                strike = atm_strike + (i * STRIKE_INTERVAL)
                strikes.append(strike)

            self.logger.debug(f"Generated {len(strikes)} strikes around ATM {atm_strike}")
            return strikes, atm_strike

        except Exception as e:
            self.logger.error(f"Error generating strikes around ATM: {e}")
            raise

    def get_otm_strike(self, option_type: str, points_away: int, spot_price: float = None) -> int:
        """
        Get Out-of-The-Money strike (DYNAMIC)

        Args:
            option_type: 'CE' or 'PE'
            points_away: How many points away from ATM (in terms of strike intervals)
            spot_price: Current spot price

        Returns:
            OTM strike

        Example:
            >>> # Get 2 strikes OTM Call (above ATM)
            >>> otm_ce = market_data.get_otm_strike('CE', points_away=2)
            >>> # If ATM is 24150, this returns 24250 (24150 + 2*50)
        """
        try:
            atm_strike = self.calculate_atm_strike(spot_price)

            if option_type.upper() == 'CE':
                # Calls: OTM is above ATM
                otm_strike = atm_strike + (points_away * STRIKE_INTERVAL)
            elif option_type.upper() == 'PE':
                # Puts: OTM is below ATM
                otm_strike = atm_strike - (points_away * STRIKE_INTERVAL)
            else:
                raise ValueError(f"Invalid option_type: {option_type}. Must be 'CE' or 'PE'")

            self.logger.debug(f"OTM {option_type} Strike: {otm_strike} ({points_away} strikes from ATM)")
            return int(otm_strike)

        except Exception as e:
            self.logger.error(f"Error calculating OTM strike: {e}")
            raise

    def get_itm_strike(self, option_type: str, points_away: int, spot_price: float = None) -> int:
        """
        Get In-The-Money strike (DYNAMIC)

        Args:
            option_type: 'CE' or 'PE'
            points_away: How many points away from ATM (in terms of strike intervals)
            spot_price: Current spot price

        Returns:
            ITM strike

        Example:
            >>> # Get 2 strikes ITM Call (below ATM)
            >>> itm_ce = market_data.get_itm_strike('CE', points_away=2)
            >>> # If ATM is 24150, this returns 24050 (24150 - 2*50)
        """
        try:
            atm_strike = self.calculate_atm_strike(spot_price)

            if option_type.upper() == 'CE':
                # Calls: ITM is below ATM
                itm_strike = atm_strike - (points_away * STRIKE_INTERVAL)
            elif option_type.upper() == 'PE':
                # Puts: ITM is above ATM
                itm_strike = atm_strike + (points_away * STRIKE_INTERVAL)
            else:
                raise ValueError(f"Invalid option_type: {option_type}. Must be 'CE' or 'PE'")

            self.logger.debug(f"ITM {option_type} Strike: {itm_strike} ({points_away} strikes from ATM)")
            return int(itm_strike)

        except Exception as e:
            self.logger.error(f"Error calculating ITM strike: {e}")
            raise

    # =========================================================================
    # MARKET STATUS & TIMING
    # =========================================================================

    def is_market_open(self) -> bool:
        """
        Check if market is currently open (DYNAMIC)

        Returns:
            True if market is open for trading
        """
        try:
            now = datetime.now(self.tz)
            current_time = now.time()

            # Check if it's a weekday (Monday=0, Sunday=6)
            if now.weekday() >= 5:  # Saturday or Sunday
                return False

            # Parse trading hours
            market_open = datetime.strptime(MARKET_OPEN_TIME, "%H:%M").time()
            market_close = datetime.strptime(MARKET_CLOSE_TIME, "%H:%M").time()

            # Check if current time is within market hours
            is_open = market_open <= current_time <= market_close

            return is_open

        except Exception as e:
            self.logger.error(f"Error checking market status: {e}")
            return False

    def is_trading_allowed(self) -> bool:
        """
        Check if trading is allowed based on configured trading hours (DYNAMIC)
        (Avoids first 5 minutes and last 10 minutes)

        Returns:
            True if trading is allowed
        """
        try:
            now = datetime.now(self.tz)
            current_time = now.time()

            # Check if market is open
            if not self.is_market_open():
                return False

            # Parse trading window
            trading_start = datetime.strptime(TRADING_START_TIME, "%H:%M").time()
            trading_end = datetime.strptime(TRADING_END_TIME, "%H:%M").time()

            # Check if current time is within trading window
            allowed = trading_start <= current_time <= trading_end

            if not allowed:
                self.logger.debug(f"Trading not allowed at {current_time}. Window: {trading_start}-{trading_end}")

            return allowed

        except Exception as e:
            self.logger.error(f"Error checking trading window: {e}")
            return False

    def time_to_market_close(self) -> int:
        """
        Get minutes remaining until market close (DYNAMIC)

        Returns:
            Minutes until market close (0 if market is closed)
        """
        try:
            now = datetime.now(self.tz)

            if not self.is_market_open():
                return 0

            # Parse market close time
            market_close = datetime.strptime(MARKET_CLOSE_TIME, "%H:%M").time()
            close_datetime = datetime.combine(now.date(), market_close)
            close_datetime = self.tz.localize(close_datetime)

            # Calculate difference
            diff = close_datetime - now
            minutes = int(diff.total_seconds() / 60)

            return max(0, minutes)

        except Exception as e:
            self.logger.error(f"Error calculating time to market close: {e}")
            return 0

    def should_force_exit(self) -> bool:
        """
        Check if positions should be force-exited (near market close)

        Returns:
            True if force exit time has been reached
        """
        try:
            minutes_to_close = self.time_to_market_close()

            # Force exit if less than 5 minutes to close
            should_exit = minutes_to_close <= 5

            if should_exit:
                self.logger.warning(f"Force exit triggered! {minutes_to_close} minutes to market close")

            return should_exit

        except Exception as e:
            self.logger.error(f"Error checking force exit condition: {e}")
            return False

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_market_status_summary(self) -> Dict:
        """
        Get comprehensive market status summary (DYNAMIC)

        Returns:
            Dictionary with market status information
        """
        try:
            spot_price = self.get_nifty_spot_price()
            atm_strike = self.calculate_atm_strike(spot_price)
            ohlc = self.get_nifty_ohlc()

            summary = {
                'timestamp': datetime.now(self.tz).isoformat(),
                'market_open': self.is_market_open(),
                'trading_allowed': self.is_trading_allowed(),
                'minutes_to_close': self.time_to_market_close(),
                'should_force_exit': self.should_force_exit(),
                'nifty_spot': spot_price,
                'atm_strike': atm_strike,
                'open': ohlc.get('open'),
                'high': ohlc.get('high'),
                'low': ohlc.get('low'),
                'change_percent': ((spot_price - ohlc.get('open', spot_price)) / ohlc.get('open', spot_price)) * 100 if ohlc.get('open') else 0
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error getting market status summary: {e}")
            return {}

    def clear_cache(self):
        """Clear data cache"""
        self._cache.clear()
        self.logger.debug("Market data cache cleared")


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Market Data Module...")
    print("="*60)

    try:
        # Initialize (requires valid Kite credentials)
        from src.api.kite_wrapper import KiteWrapper
        from config.config import KITE_ACCESS_TOKEN

        if not KITE_ACCESS_TOKEN:
            print("⚠ No access token found. Set KITE_ACCESS_TOKEN in config to test.")
            exit(1)

        kite = KiteWrapper()
        market_data = MarketData(kite)

        print("\n1. Testing Spot Price (DYNAMIC)")
        spot = market_data.get_nifty_spot_price()
        print(f"   Nifty Spot: {spot:,.2f}")

        print("\n2. Testing ATM Calculation (DYNAMIC)")
        atm = market_data.calculate_atm_strike()
        print(f"   ATM Strike: {atm}")

        print("\n3. Testing Strikes Around ATM (DYNAMIC)")
        strikes, atm = market_data.get_strikes_around_atm(num_strikes=3)
        print(f"   Strikes: {strikes}")
        print(f"   ATM: {atm}")

        print("\n4. Testing OTM/ITM Strikes (DYNAMIC)")
        otm_ce = market_data.get_otm_strike('CE', 2)
        otm_pe = market_data.get_otm_strike('PE', 2)
        itm_ce = market_data.get_itm_strike('CE', 1)
        itm_pe = market_data.get_itm_strike('PE', 1)
        print(f"   OTM CE (2 strikes): {otm_ce}")
        print(f"   OTM PE (2 strikes): {otm_pe}")
        print(f"   ITM CE (1 strike): {itm_ce}")
        print(f"   ITM PE (1 strike): {itm_pe}")

        print("\n5. Testing Market Status (DYNAMIC)")
        print(f"   Market Open: {market_data.is_market_open()}")
        print(f"   Trading Allowed: {market_data.is_trading_allowed()}")
        print(f"   Minutes to Close: {market_data.time_to_market_close()}")

        print("\n6. Market Status Summary")
        summary = market_data.get_market_status_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")

        print("\n" + "="*60)
        print("✓ All tests completed successfully!")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
