"""
Sample ATM Straddle Strategy
Simple example strategy for demonstration
Buy ATM Call + Put when certain conditions are met
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.strategies.base_strategy import BaseStrategy


class ATMStraddleStrategy(BaseStrategy):
    """
    Simple ATM Straddle Strategy

    Entry: Buy ATM CE + PE when Nifty is range-bound
    Exit: Target 30% profit or Stop-loss 40% loss
    """

    def __init__(self):
        super().__init__("ATM_Straddle")

        # Strategy parameters
        self.target_percent = 30  # 30% profit target
        self.stop_loss_percent = 40  # 40% stop-loss
        self.min_premium = 80  # Minimum premium per option
        self.max_premium = 200  # Maximum premium per option

    def generate_signal(self, market_data: Dict) -> Optional[Dict]:
        """
        Generate entry signal

        Args:
            market_data: Dictionary with:
                - spot_price: Current Nifty spot
                - atm_strike: ATM strike
                - atm_ce_price: ATM Call premium
                - atm_pe_price: ATM Put premium
                - volatility: Current volatility (optional)

        Returns:
            Signal dictionary or None
        """
        try:
            spot = market_data.get('spot_price', 0)
            atm_strike = market_data.get('atm_strike', 0)
            ce_price = market_data.get('atm_ce_price', 0)
            pe_price = market_data.get('atm_pe_price', 0)

            # Check if premiums are in acceptable range
            if ce_price < self.min_premium or ce_price > self.max_premium:
                return None

            if pe_price < self.min_premium or pe_price > self.max_premium:
                return None

            # Generate signal
            signal = {
                'action': 'ENTRY',
                'strategy': self.name,
                'legs': [
                    {
                        'symbol_type': 'CE',
                        'strike': atm_strike,
                        'transaction_type': 'BUY',
                        'quantity': 1,  # 1 lot
                        'price': ce_price
                    },
                    {
                        'symbol_type': 'PE',
                        'strike': atm_strike,
                        'transaction_type': 'BUY',
                        'quantity': 1,  # 1 lot
                        'price': pe_price
                    }
                ],
                'total_premium': ce_price + pe_price,
                'target': (ce_price + pe_price) * (1 + self.target_percent / 100),
                'stop_loss': (ce_price + pe_price) * (1 - self.stop_loss_percent / 100)
            }

            self.logger.info(f"Entry signal generated: ATM {atm_strike} Straddle @ ₹{ce_price + pe_price:.2f}")
            return signal

        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return None

    def should_exit(self, position: Dict, current_price: float) -> Tuple[bool, str]:
        """
        Check exit conditions

        Args:
            position: Position details with avg_price
            current_price: Current combined premium

        Returns:
            (should_exit, reason)
        """
        try:
            entry_price = position.get('avg_price', 0)

            # Calculate profit/loss percentage
            pnl_percent = ((current_price - entry_price) / entry_price) * 100

            # Check target
            if pnl_percent >= self.target_percent:
                return True, f"Target hit: {pnl_percent:.1f}%"

            # Check stop-loss
            if pnl_percent <= -self.stop_loss_percent:
                return True, f"Stop-loss hit: {pnl_percent:.1f}%"

            return False, "No exit signal"

        except Exception as e:
            self.logger.error(f"Error checking exit: {e}")
            return False, "Error"


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Sample Strategy...")

    strategy = ATMStraddleStrategy()

    # Test signal generation
    market_data = {
        'spot_price': 24150,
        'atm_strike': 24150,
        'atm_ce_price': 120,
        'atm_pe_price': 115
    }

    signal = strategy.generate_signal(market_data)
    print(f"\nSignal: {signal}")

    # Test exit check
    position = {'avg_price': 235}
    should_exit, reason = strategy.should_exit(position, 305)
    print(f"\nShould Exit: {should_exit}, Reason: {reason}")

    print("\n✓ Strategy test completed!")
