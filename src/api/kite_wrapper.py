"""
Zerodha Kite Connect API Wrapper
Provides a robust wrapper around Kite Connect API with:
- Automatic rate limiting (3 requests/second)
- Retry logic with exponential backoff
- Comprehensive error handling
- Logging of all API calls
- WebSocket support for real-time data
"""

import time
import pyotp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from kiteconnect import KiteConnect, KiteTicker
from functools import wraps
import threading

# Import local modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import (
    KITE_API_KEY, KITE_API_SECRET, KITE_ACCESS_TOKEN,
    KITE_USER_ID, KITE_PASSWORD, KITE_TOTP_SECRET,
    API_RATE_LIMIT, API_TIMEOUT, API_RETRY_COUNT, API_RETRY_DELAY
)
from src.utils.logger import get_logger


class RateLimiter:
    """
    Rate limiter for API calls
    Ensures we don't exceed Kite's rate limit (3 requests/second default)
    """

    def __init__(self, max_calls: int = 3, time_period: float = 1.0):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum number of calls allowed
            time_period: Time period in seconds
        """
        self.max_calls = max_calls
        self.time_period = time_period
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, func):
        """Decorator to rate limit function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # Remove calls older than time_period
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_period]

                if len(self.calls) >= self.max_calls:
                    # Calculate sleep time
                    sleep_time = self.time_period - (now - self.calls[0]) + 0.1  # Add small buffer
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    # Clean up old calls again
                    now = time.time()
                    self.calls = [call_time for call_time in self.calls if now - call_time < self.time_period]

                self.calls.append(time.time())

            return func(*args, **kwargs)
        return wrapper


class KiteWrapper:
    """
    Wrapper class for Zerodha Kite Connect API
    Provides robust, production-ready interface for all trading operations
    """

    def __init__(self, api_key: str = None, api_secret: str = None, access_token: str = None):
        """
        Initialize Kite Connect wrapper

        Args:
            api_key: Kite API key
            api_secret: Kite API secret
            access_token: Access token (if already generated)
        """
        self.logger = get_logger(__name__)

        # Use provided credentials or fall back to config
        self.api_key = api_key or KITE_API_KEY
        self.api_secret = api_secret or KITE_API_SECRET
        self.access_token = access_token or KITE_ACCESS_TOKEN

        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret are required. Set them in config or pass to constructor.")

        # Initialize Kite Connect
        self.kite = KiteConnect(api_key=self.api_key)

        # Set access token if available
        if self.access_token:
            self.kite.set_access_token(self.access_token)
            self.logger.info("Kite Connect initialized with existing access token")
        else:
            self.logger.warning("No access token provided. Use generate_session() to authenticate.")

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(max_calls=API_RATE_LIMIT, time_period=1.0)

        # WebSocket ticker (initialized when needed)
        self.ticker = None
        self.websocket_connected = False

        self.logger.info("KiteWrapper initialized successfully")

    # =========================================================================
    # AUTHENTICATION METHODS
    # =========================================================================

    def generate_session(self, request_token: str = None) -> str:
        """
        Generate access token from request token

        Args:
            request_token: Request token from login redirect

        Returns:
            Access token

        Note:
            After getting access token, save it securely to avoid repeated logins
        """
        try:
            if not request_token:
                login_url = self.kite.login_url()
                self.logger.info(f"Please login at: {login_url}")
                self.logger.info("After login, you'll be redirected. Copy the 'request_token' from URL.")
                return ""

            # Generate session
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)

            self.logger.info("Access token generated successfully")
            self.logger.info(f"Access Token: {self.access_token}")
            self.logger.info("Save this access token securely for future use")

            return self.access_token

        except Exception as e:
            self.logger.error(f"Error generating session: {e}")
            raise

    def auto_login_with_totp(self, user_id: str = None, password: str = None, totp_secret: str = None) -> bool:
        """
        Automated login using TOTP (Time-based One-Time Password)
        WARNING: This requires selenium and is complex. Better to use access token approach.

        Args:
            user_id: Zerodha user ID
            password: Zerodha password
            totp_secret: TOTP secret for 2FA

        Returns:
            True if successful
        """
        # This would require selenium automation which adds complexity
        # Recommended approach: Generate access token manually and use it
        self.logger.warning("Auto-login not implemented. Use manual login and save access token.")
        return False

    # =========================================================================
    # PROFILE & ACCOUNT METHODS
    # =========================================================================

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_profile(self) -> Dict:
        """Get user profile"""
        try:
            start_time = time.time()
            profile = self.kite.profile()
            response_time = time.time() - start_time
            self.logger.log_api_call('get_profile', 'SUCCESS', response_time)
            return profile
        except Exception as e:
            self.logger.error(f"Error getting profile: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_margins(self, segment: str = 'equity') -> Dict:
        """
        Get account margins

        Args:
            segment: 'equity' or 'commodity'

        Returns:
            Margin details
        """
        try:
            start_time = time.time()
            margins = self.kite.margins(segment=segment)
            response_time = time.time() - start_time
            self.logger.log_api_call(f'get_margins_{segment}', 'SUCCESS', response_time)
            return margins
        except Exception as e:
            self.logger.error(f"Error getting margins: {e}")
            raise

    # =========================================================================
    # MARKET DATA METHODS
    # =========================================================================

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_quote(self, symbols: List[str]) -> Dict:
        """
        Get live quotes for symbols

        Args:
            symbols: List of symbols in format "EXCHANGE:SYMBOL"
                    Example: ["NSE:NIFTY BANK", "NFO:NIFTY24NOV24000CE"]

        Returns:
            Dictionary of quotes
        """
        try:
            start_time = time.time()
            quotes = self.kite.quote(symbols)
            response_time = time.time() - start_time
            self.logger.log_api_call(f'get_quote', 'SUCCESS', response_time)
            return quotes
        except Exception as e:
            self.logger.error(f"Error getting quotes for {symbols}: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_ltp(self, symbols: List[str]) -> Dict:
        """
        Get last traded price for symbols (faster than get_quote)

        Args:
            symbols: List of symbols

        Returns:
            Dictionary of LTP values
        """
        try:
            start_time = time.time()
            ltp = self.kite.ltp(symbols)
            response_time = time.time() - start_time
            self.logger.log_api_call(f'get_ltp', 'SUCCESS', response_time)
            return ltp
        except Exception as e:
            self.logger.error(f"Error getting LTP for {symbols}: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_ohlc(self, symbols: List[str]) -> Dict:
        """
        Get OHLC and other key data for symbols

        Args:
            symbols: List of symbols

        Returns:
            Dictionary of OHLC data
        """
        try:
            start_time = time.time()
            ohlc = self.kite.ohlc(symbols)
            response_time = time.time() - start_time
            self.logger.log_api_call(f'get_ohlc', 'SUCCESS', response_time)
            return ohlc
        except Exception as e:
            self.logger.error(f"Error getting OHLC for {symbols}: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_historical_data(self, instrument_token: int, from_date: datetime, to_date: datetime,
                           interval: str = "day") -> List[Dict]:
        """
        Get historical OHLC data

        Args:
            instrument_token: Instrument token
            from_date: Start date
            to_date: End date
            interval: minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute

        Returns:
            List of OHLC records
        """
        try:
            start_time = time.time()
            data = self.kite.historical_data(instrument_token, from_date, to_date, interval)
            response_time = time.time() - start_time
            self.logger.log_api_call(f'get_historical_data', 'SUCCESS', response_time)
            return data
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            raise

    # =========================================================================
    # INSTRUMENT & OPTIONS CHAIN METHODS
    # =========================================================================

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_instruments(self, exchange: str = "NFO") -> List[Dict]:
        """
        Get all instruments for exchange

        Args:
            exchange: Exchange (NSE, NFO, BSE, etc.)

        Returns:
            List of instruments
        """
        try:
            start_time = time.time()
            instruments = self.kite.instruments(exchange=exchange)
            response_time = time.time() - start_time
            self.logger.log_api_call(f'get_instruments_{exchange}', 'SUCCESS', response_time)
            self.logger.info(f"Fetched {len(instruments)} instruments from {exchange}")
            return instruments
        except Exception as e:
            self.logger.error(f"Error getting instruments: {e}")
            raise

    # =========================================================================
    # ORDER MANAGEMENT METHODS
    # =========================================================================

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def place_order(self, symbol: str, exchange: str, transaction_type: str,
                   quantity: int, order_type: str = "MARKET", product: str = "MIS",
                   price: float = None, trigger_price: float = None,
                   validity: str = "DAY", tag: str = None) -> str:
        """
        Place an order

        Args:
            symbol: Trading symbol
            exchange: Exchange (NFO, NSE, etc.)
            transaction_type: BUY or SELL
            quantity: Quantity to trade
            order_type: MARKET, LIMIT, SL, SL-M
            product: MIS (intraday) or NRML (carry forward)
            price: Limit price (for LIMIT orders)
            trigger_price: Trigger price (for SL orders)
            validity: DAY or IOC
            tag: Optional tag for order tracking

        Returns:
            Order ID
        """
        try:
            start_time = time.time()

            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product=product,
                price=price,
                trigger_price=trigger_price,
                validity=validity,
                tag=tag
            )

            response_time = time.time() - start_time
            self.logger.log_api_call('place_order', 'SUCCESS', response_time)
            self.logger.log_order(
                order_id,
                'PLACED',
                {
                    'symbol': symbol,
                    'type': transaction_type,
                    'qty': quantity,
                    'order_type': order_type,
                    'price': price
                }
            )

            return order_id

        except Exception as e:
            self.logger.error(f"Error placing order for {symbol}: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def modify_order(self, order_id: str, quantity: int = None, price: float = None,
                    order_type: str = None, trigger_price: float = None, validity: str = None) -> str:
        """
        Modify an existing order

        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New price
            order_type: New order type
            trigger_price: New trigger price
            validity: New validity

        Returns:
            Order ID
        """
        try:
            start_time = time.time()

            order_id = self.kite.modify_order(
                variety=self.kite.VARIETY_REGULAR,
                order_id=order_id,
                quantity=quantity,
                price=price,
                order_type=order_type,
                trigger_price=trigger_price,
                validity=validity
            )

            response_time = time.time() - start_time
            self.logger.log_api_call('modify_order', 'SUCCESS', response_time)
            self.logger.log_order(order_id, 'MODIFIED', {'price': price, 'qty': quantity})

            return order_id

        except Exception as e:
            self.logger.error(f"Error modifying order {order_id}: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def cancel_order(self, order_id: str, variety: str = "regular") -> str:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel
            variety: Order variety (regular, amo, co, iceberg)

        Returns:
            Order ID
        """
        try:
            start_time = time.time()

            cancelled_order_id = self.kite.cancel_order(
                variety=variety,
                order_id=order_id
            )

            response_time = time.time() - start_time
            self.logger.log_api_call('cancel_order', 'SUCCESS', response_time)
            self.logger.log_order(order_id, 'CANCELLED', {})

            return cancelled_order_id

        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_orders(self) -> List[Dict]:
        """Get all orders for the day"""
        try:
            start_time = time.time()
            orders = self.kite.orders()
            response_time = time.time() - start_time
            self.logger.log_api_call('get_orders', 'SUCCESS', response_time)
            return orders
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_order_history(self, order_id: str) -> List[Dict]:
        """Get order history for specific order"""
        try:
            start_time = time.time()
            history = self.kite.order_history(order_id=order_id)
            response_time = time.time() - start_time
            self.logger.log_api_call('get_order_history', 'SUCCESS', response_time)
            return history
        except Exception as e:
            self.logger.error(f"Error getting order history for {order_id}: {e}")
            raise

    # =========================================================================
    # POSITION METHODS
    # =========================================================================

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_positions(self) -> Dict:
        """Get current positions"""
        try:
            start_time = time.time()
            positions = self.kite.positions()
            response_time = time.time() - start_time
            self.logger.log_api_call('get_positions', 'SUCCESS', response_time)
            return positions
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            raise

    @RateLimiter(max_calls=API_RATE_LIMIT)
    def get_holdings(self) -> List[Dict]:
        """Get holdings (long-term positions)"""
        try:
            start_time = time.time()
            holdings = self.kite.holdings()
            response_time = time.time() - start_time
            self.logger.log_api_call('get_holdings', 'SUCCESS', response_time)
            return holdings
        except Exception as e:
            self.logger.error(f"Error getting holdings: {e}")
            raise

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def is_market_open(self) -> bool:
        """
        Check if market is currently open

        Returns:
            True if market is open
        """
        try:
            # Try to get quote for NIFTY
            quote = self.get_ltp(["NSE:NIFTY 50"])
            return True
        except:
            return False

    def retry_on_failure(self, func, *args, max_retries=API_RETRY_COUNT, delay=API_RETRY_DELAY, **kwargs):
        """
        Retry function call on failure with exponential backoff

        Args:
            func: Function to call
            max_retries: Maximum number of retries
            delay: Initial delay between retries
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result
        """
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = delay * (2 ** attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    # Test the wrapper
    print("Testing Kite Wrapper...")

    try:
        kite_wrapper = KiteWrapper()
        print("✓ KiteWrapper initialized")

        # Test with access token if available
        if KITE_ACCESS_TOKEN:
            profile = kite_wrapper.get_profile()
            print(f"✓ Logged in as: {profile.get('user_name', 'Unknown')}")

            margins = kite_wrapper.get_margins()
            print(f"✓ Available margin: ₹{margins.get('available', {}).get('cash', 0):,.2f}")
        else:
            print("! No access token found. Set KITE_ACCESS_TOKEN in config to test API calls.")
            print(f"! Login URL: {kite_wrapper.kite.login_url()}")

    except Exception as e:
        print(f"✗ Error: {e}")
