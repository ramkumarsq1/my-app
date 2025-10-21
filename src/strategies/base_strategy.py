"""
Base Strategy Class
Abstract base class for all trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger


class BaseStrategy(ABC):
    """
    Abstract Base Strategy Class
    All strategies must inherit from this class
    """

    def __init__(self, name: str):
        """
        Initialize strategy

        Args:
            name: Strategy name
        """
        self.name = name
        self.logger = get_logger(f"Strategy.{name}")
        self.enabled = True

        self.logger.info(f"Strategy '{name}' initialized")

    @abstractmethod
    def generate_signal(self, market_data: Dict) -> Optional[Dict]:
        """
        Generate trading signal

        Args:
            market_data: Dictionary with market data

        Returns:
            Signal dictionary with keys: action, symbol, quantity, price, etc.
            None if no signal
        """
        pass

    @abstractmethod
    def should_exit(self, position: Dict, current_price: float) -> Tuple[bool, str]:
        """
        Check if position should be exited

        Args:
            position: Position dictionary
            current_price: Current market price

        Returns:
            Tuple of (should_exit: bool, reason: str)
        """
        pass

    def enable(self):
        """Enable strategy"""
        self.enabled = True
        self.logger.info(f"Strategy '{self.name}' ENABLED")

    def disable(self):
        """Disable strategy"""
        self.enabled = False
        self.logger.info(f"Strategy '{self.name}' DISABLED")

    def is_enabled(self) -> bool:
        """Check if strategy is enabled"""
        return self.enabled
