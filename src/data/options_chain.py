"""
Options Chain Manager
Handles all options-related operations:
- Dynamic weekly expiry detection (auto-detects current Thursday)
- Options symbol generation (based on current week/month)
- Options chain data fetching
- Strike selection and filtering
- Greeks calculation
- Premium and volume analysis
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import pytz
from calendar import monthrange

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import (
    TRADING_SYMBOL, EXCHANGE, STRIKE_INTERVAL, ATM_STRIKE_RANGE,
    MIN_OPTION_VOLUME, MIN_OPEN_INTEREST, TIMEZONE
)
from src.utils.logger import get_logger
from src.api.kite_wrapper import KiteWrapper
from src.data.market_data import MarketData


class OptionsChain:
    """
    Options Chain Manager
    Everything is DYNAMIC - based on current market data
    """

    def __init__(self, kite_wrapper: KiteWrapper, market_data: MarketData):
        """
        Initialize Options Chain Manager

        Args:
            kite_wrapper: Initialized KiteWrapper instance
            market_data: Initialized MarketData instance
        """
        self.kite = kite_wrapper
        self.market_data = market_data
        self.logger = get_logger(__name__)

        self.tz = pytz.timezone(TIMEZONE)

        # Cache for instruments list (to avoid repeated API calls)
        self._instruments_cache = None
        self._instruments_cache_time = None
        self._cache_validity_hours = 24  # Refresh once a day

        self.logger.info("OptionsChain initialized")

    # =========================================================================
    # WEEKLY EXPIRY DETECTION (DYNAMIC)
    # =========================================================================

    def get_current_weekly_expiry(self) -> datetime:
        """
        Get current week's expiry date (DYNAMIC)
        Nifty weekly options expire every Thursday (or next trading day if holiday)

        Returns:
            datetime object of current week's expiry

        Example:
            >>> expiry = options_chain.get_current_weekly_expiry()
            >>> print(expiry.strftime('%d-%b-%Y'))
            '21-NOV-2024'
        """
        try:
            today = datetime.now(self.tz).date()
            days_ahead = 3 - today.weekday()  # 3 = Thursday (Monday=0)

            if days_ahead < 0:  # If today is Friday or later
                days_ahead += 7

            expiry = today + timedelta(days=days_ahead)

            self.logger.debug(f"Current weekly expiry: {expiry}")
            return datetime.combine(expiry, datetime.min.time())

        except Exception as e:
            self.logger.error(f"Error calculating weekly expiry: {e}")
            raise

    def get_next_weekly_expiry(self) -> datetime:
        """
        Get next week's expiry date (DYNAMIC)

        Returns:
            datetime object of next week's expiry
        """
        try:
            current_expiry = self.get_current_weekly_expiry()
            next_expiry = current_expiry + timedelta(days=7)

            self.logger.debug(f"Next weekly expiry: {next_expiry.date()}")
            return next_expiry

        except Exception as e:
            self.logger.error(f"Error calculating next weekly expiry: {e}")
            raise

    def get_monthly_expiry(self, year: int = None, month: int = None) -> datetime:
        """
        Get monthly expiry (last Thursday of the month)

        Args:
            year: Year (current year if None)
            month: Month (current month if None)

        Returns:
            datetime object of monthly expiry
        """
        try:
            now = datetime.now(self.tz)
            year = year or now.year
            month = month or now.month

            # Get last day of month
            last_day = monthrange(year, month)[1]

            # Find last Thursday
            last_date = datetime(year, month, last_day)
            days_back = (last_date.weekday() - 3) % 7
            monthly_expiry = last_date - timedelta(days=days_back)

            self.logger.debug(f"Monthly expiry for {month}/{year}: {monthly_expiry.date()}")
            return monthly_expiry

        except Exception as e:
            self.logger.error(f"Error calculating monthly expiry: {e}")
            raise

    def is_monthly_expiry_week(self) -> bool:
        """
        Check if current week's expiry is also monthly expiry

        Returns:
            True if weekly expiry coincides with monthly expiry
        """
        try:
            weekly_expiry = self.get_current_weekly_expiry()
            monthly_expiry = self.get_monthly_expiry()

            is_monthly = weekly_expiry.date() == monthly_expiry.date()

            if is_monthly:
                self.logger.info("Current week is MONTHLY expiry week")

            return is_monthly

        except Exception as e:
            self.logger.error(f"Error checking monthly expiry week: {e}")
            return False

    def is_expiry_day(self) -> bool:
        """
        Check if today is expiry day (DYNAMIC)

        Returns:
            True if today is expiry day
        """
        try:
            today = datetime.now(self.tz).date()
            expiry = self.get_current_weekly_expiry().date()

            return today == expiry

        except Exception as e:
            self.logger.error(f"Error checking expiry day: {e}")
            return False

    # =========================================================================
    # OPTIONS SYMBOL GENERATION (DYNAMIC)
    # =========================================================================

    def generate_option_symbol(self, strike: int, option_type: str, expiry: datetime = None) -> str:
        """
        Generate option trading symbol (DYNAMIC based on current expiry)

        Format: NIFTY[YY][MMM][STRIKE][CE/PE]
        Example: NIFTY24NOV24000CE

        Args:
            strike: Strike price
            option_type: 'CE' or 'PE'
            expiry: Expiry date (uses current weekly expiry if None)

        Returns:
            Trading symbol string

        Example:
            >>> symbol = options_chain.generate_option_symbol(24000, 'CE')
            >>> print(symbol)
            'NIFTY24NOV24000CE'
        """
        try:
            if expiry is None:
                expiry = self.get_current_weekly_expiry()

            # Format: NIFTY[YY][MMM][STRIKE][CE/PE]
            year = expiry.strftime('%y')  # 24
            month = expiry.strftime('%b').upper()  # NOV
            option_type = option_type.upper()

            if option_type not in ['CE', 'PE']:
                raise ValueError(f"Invalid option_type: {option_type}. Must be 'CE' or 'PE'")

            symbol = f"{TRADING_SYMBOL}{year}{month}{strike}{option_type}"

            self.logger.debug(f"Generated symbol: {symbol}")
            return symbol

        except Exception as e:
            self.logger.error(f"Error generating option symbol: {e}")
            raise

    def generate_option_symbols_for_strikes(self, strikes: List[int], option_type: str = 'BOTH') -> List[str]:
        """
        Generate option symbols for multiple strikes

        Args:
            strikes: List of strike prices
            option_type: 'CE', 'PE', or 'BOTH'

        Returns:
            List of trading symbols
        """
        try:
            symbols = []

            for strike in strikes:
                if option_type in ['CE', 'BOTH']:
                    symbols.append(self.generate_option_symbol(strike, 'CE'))
                if option_type in ['PE', 'BOTH']:
                    symbols.append(self.generate_option_symbol(strike, 'PE'))

            self.logger.debug(f"Generated {len(symbols)} option symbols")
            return symbols

        except Exception as e:
            self.logger.error(f"Error generating option symbols: {e}")
            raise

    # =========================================================================
    # OPTIONS DATA FETCHING (DYNAMIC)
    # =========================================================================

    def get_option_chain_data(self, strikes: List[int] = None, num_strikes: int = 5) -> pd.DataFrame:
        """
        Get options chain data for specified strikes or around ATM (DYNAMIC)

        Args:
            strikes: List of strikes (generates around ATM if None)
            num_strikes: Number of strikes around ATM if strikes not provided

        Returns:
            DataFrame with options chain data
        """
        try:
            # Get strikes if not provided
            if strikes is None:
                strikes, atm = self.market_data.get_strikes_around_atm(num_strikes)

            # Generate symbols
            symbols = self.generate_option_symbols_for_strikes(strikes, option_type='BOTH')

            # Prepare symbols with exchange prefix for Kite API
            exchange_symbols = [f"{EXCHANGE}:{symbol}" for symbol in symbols]

            # Fetch quotes
            self.logger.info(f"Fetching options chain data for {len(symbols)} symbols...")
            quotes = self.kite.get_quote(exchange_symbols)

            # Parse into DataFrame
            chain_data = []
            for symbol in symbols:
                full_symbol = f"{EXCHANGE}:{symbol}"
                if full_symbol not in quotes:
                    continue

                quote = quotes[full_symbol]

                # Extract strike and type from symbol
                # Format: NIFTY24NOV24000CE
                option_type = symbol[-2:]  # CE or PE
                strike_str = symbol[:-2]  # NIFTY24NOV24000
                strike = int(''.join(filter(str.isdigit, strike_str[-5:])))  # Get last 5 digits

                chain_data.append({
                    'symbol': symbol,
                    'strike': strike,
                    'type': option_type,
                    'ltp': quote.get('last_price', 0),
                    'volume': quote.get('volume', 0),
                    'oi': quote.get('oi', 0),
                    'bid': quote.get('depth', {}).get('buy', [{}])[0].get('price', 0) if quote.get('depth') else 0,
                    'ask': quote.get('depth', {}).get('sell', [{}])[0].get('price', 0) if quote.get('depth') else 0,
                    'change': quote.get('net_change', 0),
                    'change_percent': quote.get('change', 0),
                })

            df = pd.DataFrame(chain_data)

            if len(df) > 0:
                # Sort by strike and type
                df = df.sort_values(['strike', 'type'], ascending=[True, False])
                self.logger.info(f"Fetched options chain data: {len(df)} options")
            else:
                self.logger.warning("No options chain data received")

            return df

        except Exception as e:
            self.logger.error(f"Error fetching options chain data: {e}")
            raise

    def get_option_quote(self, strike: int, option_type: str) -> Dict:
        """
        Get quote for a specific option (DYNAMIC)

        Args:
            strike: Strike price
            option_type: 'CE' or 'PE'

        Returns:
            Quote dictionary
        """
        try:
            symbol = self.generate_option_symbol(strike, option_type)
            full_symbol = f"{EXCHANGE}:{symbol}"

            quote = self.kite.get_quote([full_symbol])
            return quote.get(full_symbol, {})

        except Exception as e:
            self.logger.error(f"Error fetching option quote for {strike}{option_type}: {e}")
            raise

    def get_option_ltp(self, strike: int, option_type: str) -> float:
        """
        Get last traded price for specific option (DYNAMIC)

        Args:
            strike: Strike price
            option_type: 'CE' or 'PE'

        Returns:
            Last traded price
        """
        try:
            symbol = self.generate_option_symbol(strike, option_type)
            full_symbol = f"{EXCHANGE}:{symbol}"

            ltp_data = self.kite.get_ltp([full_symbol])
            ltp = ltp_data.get(full_symbol, {}).get('last_price', 0)

            self.logger.debug(f"{symbol} LTP: {ltp}")
            return ltp

        except Exception as e:
            self.logger.error(f"Error fetching LTP for {strike}{option_type}: {e}")
            raise

    # =========================================================================
    # STRIKE SELECTION & FILTERING (DYNAMIC)
    # =========================================================================

    def select_best_strike_by_premium(self, option_type: str, min_premium: float = 50,
                                     max_premium: float = 200, num_strikes: int = 10) -> Optional[Tuple[int, float]]:
        """
        Select best strike based on premium range (DYNAMIC)

        Args:
            option_type: 'CE' or 'PE'
            min_premium: Minimum premium
            max_premium: Maximum premium
            num_strikes: Number of strikes to check around ATM

        Returns:
            Tuple of (strike, premium) or None
        """
        try:
            # Get options chain
            chain_df = self.get_option_chain_data(num_strikes=num_strikes)

            if chain_df.empty:
                return None

            # Filter by option type and premium range
            filtered = chain_df[
                (chain_df['type'] == option_type) &
                (chain_df['ltp'] >= min_premium) &
                (chain_df['ltp'] <= max_premium)
            ]

            if filtered.empty:
                self.logger.warning(f"No {option_type} options found in premium range {min_premium}-{max_premium}")
                return None

            # Get the option closest to mid-range premium
            mid_premium = (min_premium + max_premium) / 2
            filtered['premium_diff'] = abs(filtered['ltp'] - mid_premium)
            best = filtered.loc[filtered['premium_diff'].idxmin()]

            strike = int(best['strike'])
            premium = float(best['ltp'])

            self.logger.info(f"Best strike by premium: {strike}{option_type} @ ₹{premium}")
            return (strike, premium)

        except Exception as e:
            self.logger.error(f"Error selecting strike by premium: {e}")
            return None

    def select_liquid_strikes(self, num_strikes: int = 5) -> pd.DataFrame:
        """
        Select most liquid strikes based on volume and OI (DYNAMIC)

        Args:
            num_strikes: Number of strikes to check

        Returns:
            DataFrame with liquid strikes
        """
        try:
            chain_df = self.get_option_chain_data(num_strikes=num_strikes)

            if chain_df.empty:
                return pd.DataFrame()

            # Filter by minimum volume
            liquid = chain_df[chain_df['volume'] >= MIN_OPTION_VOLUME]

            # Sort by volume
            liquid = liquid.sort_values('volume', ascending=False)

            self.logger.info(f"Found {len(liquid)} liquid options (volume >= {MIN_OPTION_VOLUME})")
            return liquid

        except Exception as e:
            self.logger.error(f"Error selecting liquid strikes: {e}")
            return pd.DataFrame()

    # =========================================================================
    # GREEKS CALCULATION (Simplified)
    # =========================================================================

    def calculate_simple_delta(self, strike: int, option_type: str, spot_price: float = None) -> float:
        """
        Calculate simplified delta (approximate)
        For accurate Greeks, use external libraries or fetch from broker

        Args:
            strike: Strike price
            option_type: 'CE' or 'PE'
            spot_price: Current spot price

        Returns:
            Approximate delta value
        """
        try:
            if spot_price is None:
                spot_price = self.market_data.get_nifty_spot_price()

            # Simplified delta calculation
            # CE: delta ≈ 0.5 at ATM, 1.0 deep ITM, 0.0 deep OTM
            # PE: delta ≈ -0.5 at ATM, -1.0 deep ITM, 0.0 deep OTM

            moneyness = (spot_price - strike) / spot_price

            if option_type.upper() == 'CE':
                if moneyness > 0.05:  # Deep ITM
                    delta = 0.9
                elif moneyness < -0.05:  # Deep OTM
                    delta = 0.1
                else:  # Around ATM
                    delta = 0.5 + (moneyness * 5)  # Approximate
            else:  # PE
                if moneyness < -0.05:  # Deep ITM
                    delta = -0.9
                elif moneyness > 0.05:  # Deep OTM
                    delta = -0.1
                else:  # Around ATM
                    delta = -0.5 - (moneyness * 5)  # Approximate

            return round(delta, 2)

        except Exception as e:
            self.logger.error(f"Error calculating delta: {e}")
            return 0.0

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_instrument_token(self, strike: int, option_type: str) -> Optional[int]:
        """
        Get instrument token for option symbol

        Args:
            strike: Strike price
            option_type: 'CE' or 'PE'

        Returns:
            Instrument token or None
        """
        try:
            symbol = self.generate_option_symbol(strike, option_type)

            # Refresh instruments cache if needed
            if self._instruments_cache is None or \
               (self._instruments_cache_time and
                (datetime.now() - self._instruments_cache_time).total_seconds() > self._cache_validity_hours * 3600):
                self._instruments_cache = self.kite.get_instruments(EXCHANGE)
                self._instruments_cache_time = datetime.now()

            # Find instrument
            for instrument in self._instruments_cache:
                if instrument['tradingsymbol'] == symbol:
                    return instrument['instrument_token']

            self.logger.warning(f"Instrument token not found for {symbol}")
            return None

        except Exception as e:
            self.logger.error(f"Error getting instrument token: {e}")
            return None


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Options Chain Module...")
    print("="*60)

    try:
        from src.api.kite_wrapper import KiteWrapper
        from config.config import KITE_ACCESS_TOKEN

        if not KITE_ACCESS_TOKEN:
            print("⚠ No access token found. Set KITE_ACCESS_TOKEN in config to test.")
            exit(1)

        kite = KiteWrapper()
        market_data = MarketData(kite)
        options_chain = OptionsChain(kite, market_data)

        print("\n1. Testing Expiry Detection (DYNAMIC)")
        weekly_expiry = options_chain.get_current_weekly_expiry()
        monthly_expiry = options_chain.get_monthly_expiry()
        print(f"   Current Weekly Expiry: {weekly_expiry.strftime('%d-%b-%Y')}")
        print(f"   Current Monthly Expiry: {monthly_expiry.strftime('%d-%b-%Y')}")
        print(f"   Is Monthly Expiry Week: {options_chain.is_monthly_expiry_week()}")
        print(f"   Is Expiry Day: {options_chain.is_expiry_day()}")

        print("\n2. Testing Symbol Generation (DYNAMIC)")
        symbol_ce = options_chain.generate_option_symbol(24000, 'CE')
        symbol_pe = options_chain.generate_option_symbol(24000, 'PE')
        print(f"   CE Symbol: {symbol_ce}")
        print(f"   PE Symbol: {symbol_pe}")

        print("\n3. Testing Options Chain Fetch (DYNAMIC)")
        chain = options_chain.get_option_chain_data(num_strikes=3)
        if not chain.empty:
            print(f"   Fetched {len(chain)} options")
            print("\n   Sample data:")
            print(chain.head(10).to_string(index=False))
        else:
            print("   No options chain data available")

        print("\n4. Testing Option LTP (DYNAMIC)")
        atm = market_data.calculate_atm_strike()
        ltp_ce = options_chain.get_option_ltp(atm, 'CE')
        ltp_pe = options_chain.get_option_ltp(atm, 'PE')
        print(f"   ATM {atm} CE: ₹{ltp_ce}")
        print(f"   ATM {atm} PE: ₹{ltp_pe}")

        print("\n" + "="*60)
        print("✓ All tests completed!")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
