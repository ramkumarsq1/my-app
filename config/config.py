"""
Configuration Management Module
Centralized configuration for the Nifty Options Trading Platform
All settings are loaded from environment variables or config.ini
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
import configparser

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Centralized configuration class
    Priority: Environment Variables > config.ini > Defaults
    """

    def __init__(self, config_file: str = None):
        """Initialize configuration"""
        self.config_file = config_file or os.path.join(Path(__file__).parent, 'config.ini')
        self.parser = configparser.ConfigParser()

        # Try to load config file if it exists
        if os.path.exists(self.config_file):
            self.parser.read(self.config_file)

    def get(self, section: str, key: str, default: Any = None, var_type: type = str) -> Any:
        """
        Get configuration value with priority: ENV > config.ini > default

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
            var_type: Type to convert the value to (str, int, float, bool)

        Returns:
            Configuration value
        """
        # Check environment variable first (format: SECTION_KEY)
        env_key = f"{section.upper()}_{key.upper()}"
        env_value = os.getenv(env_key)

        if env_value is not None:
            return self._convert_type(env_value, var_type)

        # Check config.ini file
        try:
            if self.parser.has_option(section, key):
                value = self.parser.get(section, key)
                return self._convert_type(value, var_type)
        except Exception:
            pass

        # Return default
        return default

    @staticmethod
    def _convert_type(value: str, var_type: type) -> Any:
        """Convert string value to specified type"""
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        else:
            return str(value)


# Initialize global config instance
config = Config()

# =============================================================================
# ZERODHA KITE API CREDENTIALS
# =============================================================================
KITE_API_KEY = config.get('kite', 'api_key', default='')
KITE_API_SECRET = config.get('kite', 'api_secret', default='')
KITE_ACCESS_TOKEN = config.get('kite', 'access_token', default='')
KITE_USER_ID = config.get('kite', 'user_id', default='')
KITE_PASSWORD = config.get('kite', 'password', default='')
KITE_TOTP_SECRET = config.get('kite', 'totp_secret', default='')  # For 2FA

# =============================================================================
# TRADING PARAMETERS (Dynamic, but with safe defaults)
# =============================================================================
TRADING_SYMBOL = config.get('trading', 'symbol', default='NIFTY')
EXCHANGE = config.get('trading', 'exchange', default='NFO')  # NFO for options
PRODUCT_TYPE = config.get('trading', 'product_type', default='MIS')  # MIS for intraday
ORDER_TYPE_DEFAULT = config.get('trading', 'order_type', default='MARKET')
LOT_SIZE = config.get('trading', 'lot_size', default=50, var_type=int)  # Nifty lot size
MAX_LOTS_PER_TRADE = config.get('trading', 'max_lots_per_trade', default=2, var_type=int)
MAX_OPEN_POSITIONS = config.get('trading', 'max_open_positions', default=3, var_type=int)

# =============================================================================
# RISK MANAGEMENT PARAMETERS
# =============================================================================
MAX_LOSS_PER_TRADE = config.get('risk', 'max_loss_per_trade', default=5000, var_type=float)
MAX_DAILY_LOSS = config.get('risk', 'max_daily_loss', default=15000, var_type=float)
MAX_CONSECUTIVE_LOSSES = config.get('risk', 'max_consecutive_losses', default=3, var_type=int)
STOP_LOSS_PERCENTAGE = config.get('risk', 'stop_loss_percentage', default=40, var_type=float)
TARGET_PERCENTAGE = config.get('risk', 'target_percentage', default=60, var_type=float)
MAX_MARGIN_UTILIZATION = config.get('risk', 'max_margin_utilization', default=50, var_type=float)
COOLOFF_PERIOD_MINUTES = config.get('risk', 'cooloff_period_minutes', default=30, var_type=int)

# =============================================================================
# TRADING HOURS (IST - Indian Standard Time)
# =============================================================================
MARKET_OPEN_TIME = config.get('trading_hours', 'market_open', default='09:15')
TRADING_START_TIME = config.get('trading_hours', 'trading_start', default='09:20')  # Avoid first 5 min
TRADING_END_TIME = config.get('trading_hours', 'trading_end', default='15:20')
MARKET_CLOSE_TIME = config.get('trading_hours', 'market_close', default='15:30')
FORCE_EXIT_TIME = config.get('trading_hours', 'force_exit', default='15:25')
TIMEZONE = config.get('trading_hours', 'timezone', default='Asia/Kolkata')

# =============================================================================
# OPTIONS PARAMETERS (Dynamic - will be calculated based on market data)
# =============================================================================
STRIKE_INTERVAL = config.get('options', 'strike_interval', default=50, var_type=int)
ATM_STRIKE_RANGE = config.get('options', 'atm_strike_range', default=3, var_type=int)  # strikes above/below ATM
PREFERRED_OPTION_TYPE = config.get('options', 'preferred_option_type', default='BOTH')  # CE, PE, or BOTH
MIN_OPTION_VOLUME = config.get('options', 'min_option_volume', default=10000, var_type=int)
MIN_OPEN_INTEREST = config.get('options', 'min_open_interest', default=0, var_type=int)

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_TYPE = config.get('database', 'type', default='sqlite')
DATABASE_PATH = config.get('database', 'path', default='data/trading.db')
BACKUP_ENABLED = config.get('database', 'backup_enabled', default=True, var_type=bool)

# =============================================================================
# TELEGRAM BOT CONFIGURATION
# =============================================================================
TELEGRAM_ENABLED = config.get('telegram', 'enabled', default=False, var_type=bool)
TELEGRAM_BOT_TOKEN = config.get('telegram', 'bot_token', default='')
TELEGRAM_CHAT_ID = config.get('telegram', 'chat_id', default='')
TELEGRAM_ALERTS_ENABLED = config.get('telegram', 'alerts_enabled', default=True, var_type=bool)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL = config.get('logging', 'level', default='INFO')
LOG_DIR = config.get('logging', 'dir', default='logs')
LOG_FILE_SIZE = config.get('logging', 'file_size_mb', default=10, var_type=int)
LOG_BACKUP_COUNT = config.get('logging', 'backup_count', default=5, var_type=int)
LOG_TO_CONSOLE = config.get('logging', 'console', default=True, var_type=bool)

# =============================================================================
# STRATEGY PARAMETERS
# =============================================================================
STRATEGY_NAME = config.get('strategy', 'name', default='SimpleStrategy')
STRATEGY_ENABLED = config.get('strategy', 'enabled', default=True, var_type=bool)
BACKTESTING_ENABLED = config.get('strategy', 'backtesting', default=False, var_type=bool)

# =============================================================================
# API RATE LIMITING
# =============================================================================
API_RATE_LIMIT = config.get('api', 'rate_limit', default=3, var_type=int)  # requests per second
API_TIMEOUT = config.get('api', 'timeout', default=7, var_type=int)  # seconds
API_RETRY_COUNT = config.get('api', 'retry_count', default=3, var_type=int)
API_RETRY_DELAY = config.get('api', 'retry_delay', default=1, var_type=float)  # seconds

# =============================================================================
# SAFETY SWITCHES
# =============================================================================
PAPER_TRADING = config.get('safety', 'paper_trading', default=True, var_type=bool)
TRADE_ON_EXPIRY_DAY = config.get('safety', 'trade_on_expiry', default=False, var_type=bool)
REQUIRE_CONFIRMATION = config.get('safety', 'require_confirmation', default=False, var_type=bool)
AUTO_SQUARE_OFF = config.get('safety', 'auto_square_off', default=True, var_type=bool)

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / 'config'
LOG_DIR_PATH = BASE_DIR / LOG_DIR
DATA_DIR = BASE_DIR / 'data'
BACKTEST_DIR = BASE_DIR / 'backtest'

# Create directories if they don't exist
for directory in [LOG_DIR_PATH, DATA_DIR, BACKTEST_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def validate_config() -> Dict[str, bool]:
    """
    Validate critical configuration parameters

    Returns:
        Dictionary with validation results
    """
    validation = {
        'api_credentials': bool(KITE_API_KEY and KITE_API_SECRET),
        'risk_params': MAX_DAILY_LOSS > 0 and MAX_LOSS_PER_TRADE > 0,
        'trading_params': LOT_SIZE > 0 and MAX_LOTS_PER_TRADE > 0,
        'telegram_config': (not TELEGRAM_ENABLED) or (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
    }
    return validation


def print_config(masked: bool = True):
    """
    Print current configuration (for debugging)

    Args:
        masked: Whether to mask sensitive information
    """
    print("\n" + "="*60)
    print("NIFTY OPTIONS TRADING PLATFORM - CONFIGURATION")
    print("="*60)

    print(f"\n[KITE API]")
    print(f"API Key: {'*' * 20 if masked and KITE_API_KEY else KITE_API_KEY}")
    print(f"User ID: {KITE_USER_ID}")

    print(f"\n[TRADING PARAMETERS]")
    print(f"Symbol: {TRADING_SYMBOL}")
    print(f"Exchange: {EXCHANGE}")
    print(f"Product Type: {PRODUCT_TYPE}")
    print(f"Lot Size: {LOT_SIZE}")
    print(f"Max Lots Per Trade: {MAX_LOTS_PER_TRADE}")
    print(f"Max Open Positions: {MAX_OPEN_POSITIONS}")

    print(f"\n[RISK MANAGEMENT]")
    print(f"Max Loss Per Trade: ₹{MAX_LOSS_PER_TRADE:,.0f}")
    print(f"Max Daily Loss: ₹{MAX_DAILY_LOSS:,.0f}")
    print(f"Stop Loss: {STOP_LOSS_PERCENTAGE}%")
    print(f"Target: {TARGET_PERCENTAGE}%")
    print(f"Max Margin Utilization: {MAX_MARGIN_UTILIZATION}%")

    print(f"\n[TRADING HOURS]")
    print(f"Trading Window: {TRADING_START_TIME} - {TRADING_END_TIME}")
    print(f"Force Exit Time: {FORCE_EXIT_TIME}")

    print(f"\n[SAFETY]")
    print(f"Paper Trading: {PAPER_TRADING}")
    print(f"Trade on Expiry Day: {TRADE_ON_EXPIRY_DAY}")
    print(f"Auto Square Off: {AUTO_SQUARE_OFF}")

    print(f"\n[TELEGRAM]")
    print(f"Enabled: {TELEGRAM_ENABLED}")
    print(f"Alerts: {TELEGRAM_ALERTS_ENABLED}")

    print("="*60 + "\n")


if __name__ == "__main__":
    # Validate and print configuration
    validation_results = validate_config()

    print_config(masked=True)

    print("Configuration Validation:")
    for key, value in validation_results.items():
        status = "✓ PASS" if value else "✗ FAIL"
        print(f"  {key}: {status}")
