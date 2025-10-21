"""
Logging Utility Module
Provides centralized logging for the Nifty Options Trading Platform
Features: Console + File logging, rotation, different log levels for different modules
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
import os

# Import configuration
try:
    from config.config import LOG_DIR_PATH, LOG_LEVEL, LOG_FILE_SIZE, LOG_BACKUP_COUNT, LOG_TO_CONSOLE
except ImportError:
    # Fallback defaults if config not available
    LOG_DIR_PATH = Path('logs')
    LOG_LEVEL = 'INFO'
    LOG_FILE_SIZE = 10
    LOG_BACKUP_COUNT = 5
    LOG_TO_CONSOLE = True


class TradingLogger:
    """
    Custom logger for trading platform with multiple log files for different purposes
    """

    _instances = {}

    def __init__(self, name: str = 'TradingPlatform'):
        """
        Initialize trading logger

        Args:
            name: Logger name (typically module name)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_log_level(LOG_LEVEL))
        self.logger.propagate = False

        # Ensure log directory exists
        LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handlers()

    @staticmethod
    def _get_log_level(level_str: str) -> int:
        """Convert string log level to logging constant"""
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(level_str.upper(), logging.INFO)

    def _setup_console_handler(self):
        """Setup console (stdout) handler with color coding"""
        if not LOG_TO_CONSOLE:
            return

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Custom formatter with colors (if terminal supports it)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _setup_file_handlers(self):
        """Setup rotating file handlers for different log types"""

        # Get today's date for log file names
        today = datetime.now().strftime('%Y%m%d')

        # 1. Main application log (INFO and above)
        main_log = LOG_DIR_PATH / f'trading_{today}.log'
        main_handler = RotatingFileHandler(
            main_log,
            maxBytes=LOG_FILE_SIZE * 1024 * 1024,  # Convert MB to bytes
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.INFO)
        main_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        main_handler.setFormatter(main_formatter)
        self.logger.addHandler(main_handler)

        # 2. Error log (ERROR and above)
        error_log = LOG_DIR_PATH / f'errors_{today}.log'
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=LOG_FILE_SIZE * 1024 * 1024,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(main_formatter)
        self.logger.addHandler(error_handler)

        # 3. Trade log (special logger for all trade-related activities)
        if self.name in ['OrderManager', 'PositionManager', 'TradingEngine', 'StrategyEngine']:
            trade_log = LOG_DIR_PATH / f'trades_{today}.log'
            trade_handler = RotatingFileHandler(
                trade_log,
                maxBytes=LOG_FILE_SIZE * 1024 * 1024,
                backupCount=30,  # Keep 30 days of trade logs
                encoding='utf-8'
            )
            trade_handler.setLevel(logging.INFO)
            trade_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            trade_handler.setFormatter(trade_formatter)
            self.logger.addHandler(trade_handler)

    # Convenience methods
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, **kwargs)

    # Trade-specific logging methods
    def log_trade(self, action: str, symbol: str, quantity: int, price: float, **kwargs):
        """
        Log trade execution

        Args:
            action: BUY or SELL
            symbol: Trading symbol
            quantity: Quantity traded
            price: Execution price
            **kwargs: Additional trade details
        """
        trade_info = f"TRADE | {action} | {symbol} | Qty: {quantity} | Price: {price}"
        if kwargs:
            trade_info += f" | {kwargs}"
        self.info(trade_info)

    def log_order(self, order_id: str, status: str, details: dict):
        """
        Log order status

        Args:
            order_id: Order ID
            status: Order status
            details: Order details dictionary
        """
        self.info(f"ORDER | ID: {order_id} | Status: {status} | Details: {details}")

    def log_position(self, symbol: str, quantity: int, avg_price: float, pnl: float):
        """
        Log position update

        Args:
            symbol: Trading symbol
            quantity: Current quantity
            avg_price: Average price
            pnl: Current P&L
        """
        self.info(f"POSITION | {symbol} | Qty: {quantity} | Avg: {avg_price} | P&L: ₹{pnl:.2f}")

    def log_risk_event(self, event_type: str, message: str, severity: str = 'WARNING'):
        """
        Log risk management event

        Args:
            event_type: Type of risk event
            message: Event message
            severity: Severity level
        """
        log_message = f"RISK | {event_type} | {message}"
        if severity == 'CRITICAL':
            self.critical(log_message)
        elif severity == 'ERROR':
            self.error(log_message)
        else:
            self.warning(log_message)

    def log_strategy_signal(self, strategy_name: str, signal_type: str, symbol: str, details: dict):
        """
        Log strategy signal

        Args:
            strategy_name: Name of strategy
            signal_type: ENTRY or EXIT
            symbol: Trading symbol
            details: Signal details
        """
        self.info(f"SIGNAL | {strategy_name} | {signal_type} | {symbol} | {details}")

    def log_api_call(self, endpoint: str, status: str, response_time: float = None):
        """
        Log API call

        Args:
            endpoint: API endpoint
            status: Success or error status
            response_time: Response time in seconds
        """
        msg = f"API | {endpoint} | {status}"
        if response_time:
            msg += f" | {response_time:.3f}s"
        self.debug(msg)


def get_logger(name: str = 'TradingPlatform') -> TradingLogger:
    """
    Get or create logger instance (singleton pattern per name)

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        TradingLogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Trading started")
    """
    if name not in TradingLogger._instances:
        TradingLogger._instances[name] = TradingLogger(name)
    return TradingLogger._instances[name]


# Create a default logger instance
logger = get_logger('TradingPlatform')


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    # Test the logger
    test_logger = get_logger('TestLogger')

    test_logger.info("Testing info message")
    test_logger.warning("Testing warning message")
    test_logger.error("Testing error message")

    # Test trade logging
    test_logger.log_trade('BUY', 'NIFTY24NOV24000CE', 50, 150.50, strategy='TestStrategy')

    # Test order logging
    test_logger.log_order('ORDER123', 'COMPLETE', {'price': 150.50, 'qty': 50})

    # Test position logging
    test_logger.log_position('NIFTY24NOV24000CE', 50, 150.50, 2500.00)

    # Test risk event logging
    test_logger.log_risk_event('DAILY_LOSS_LIMIT', 'Daily loss limit reached', severity='CRITICAL')

    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception as e:
        test_logger.exception(f"Caught exception: {e}")

    print(f"\nLogs written to: {LOG_DIR_PATH}")
    print("Check the following files:")
    print(f"  - trading_{datetime.now().strftime('%Y%m%d')}.log")
    print(f"  - errors_{datetime.now().strftime('%Y%m%d')}.log")
    print(f"  - trades_{datetime.now().strftime('%Y%m%d')}.log (if applicable)")
