"""
Position Manager
Tracks and manages trading positions:
- Real-time position tracking
- P&L calculation (realized & unrealized)
- Position squareoff
- Average price calculation
- Multi-leg position handling
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import LOT_SIZE, PAPER_TRADING
from src.utils.logger import get_logger
from src.api.kite_wrapper import KiteWrapper
from src.data.options_chain import OptionsChain


@dataclass
class Position:
    """Position data class"""
    symbol: str
    quantity: int  # Positive for long, negative for short
    avg_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    entry_time: datetime = None


class PositionManager:
    """
    Position Manager
    Tracks all open and closed positions with P&L
    """

    def __init__(self, kite_wrapper: KiteWrapper, options_chain: OptionsChain, paper_trading: bool = None):
        """
        Initialize Position Manager

        Args:
            kite_wrapper: Initialized KiteWrapper instance
            options_chain: Initialized OptionsChain instance
            paper_trading: Paper trading mode
        """
        self.kite = kite_wrapper
        self.options = options_chain
        self.logger = get_logger(__name__)

        self.paper_trading = paper_trading if paper_trading is not None else PAPER_TRADING

        # Position tracking
        self.positions: Dict[str, Position] = {}  # symbol: Position
        self.closed_positions: List[Position] = []

        # Daily P&L tracking
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

        if self.paper_trading:
            self.logger.warning("Position Manager in PAPER TRADING mode")

        self.logger.info("PositionManager initialized")

    # =========================================================================
    # POSITION UPDATES
    # =========================================================================

    def update_position(self, symbol: str, transaction_type: str, quantity: int, price: float):
        """
        Update position after a trade

        Args:
            symbol: Trading symbol
            transaction_type: 'BUY' or 'SELL'
            quantity: Quantity traded (in lots)
            price: Execution price
        """
        try:
            qty = quantity * LOT_SIZE

            if symbol not in self.positions:
                # New position
                position_qty = qty if transaction_type == 'BUY' else -qty
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=position_qty,
                    avg_price=price,
                    entry_time=datetime.now()
                )
                self.logger.info(f"New position opened: {symbol} - Qty: {position_qty}, Price: ₹{price}")

            else:
                # Update existing position
                position = self.positions[symbol]
                traded_qty = qty if transaction_type == 'BUY' else -qty

                # Check if this is closing or adding to position
                if (position.quantity > 0 and traded_qty < 0) or (position.quantity < 0 and traded_qty > 0):
                    # Closing position (partial or full)
                    self._close_position(symbol, abs(traded_qty), price)
                else:
                    # Adding to position
                    total_cost = (position.quantity * position.avg_price) + (traded_qty * price)
                    position.quantity += traded_qty
                    if position.quantity != 0:
                        position.avg_price = total_cost / position.quantity

                    self.logger.info(f"Position updated: {symbol} - New Qty: {position.quantity}, Avg: ₹{position.avg_price:.2f}")

            self.logger.log_position(symbol, self.positions[symbol].quantity, self.positions[symbol].avg_price, 0)

        except Exception as e:
            self.logger.error(f"Error updating position for {symbol}: {e}")

    def _close_position(self, symbol: str, closing_qty: int, exit_price: float):
        """
        Close position (partial or full)

        Args:
            symbol: Trading symbol
            closing_qty: Quantity to close
            exit_price: Exit price
        """
        try:
            if symbol not in self.positions:
                self.logger.warning(f"No position found for {symbol}")
                return

            position = self.positions[symbol]
            position_qty = abs(position.quantity)

            if closing_qty >= position_qty:
                # Full exit
                realized_pnl = self._calculate_realized_pnl(position, position_qty, exit_price)
                position.realized_pnl = realized_pnl
                self.daily_pnl += realized_pnl

                # Track trade stats
                self.total_trades += 1
                if realized_pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1

                self.logger.info(f"Position CLOSED: {symbol} - P&L: ₹{realized_pnl:.2f}")
                self.logger.log_position(symbol, 0, exit_price, realized_pnl)

                # Move to closed positions
                self.closed_positions.append(position)
                del self.positions[symbol]

            else:
                # Partial exit
                realized_pnl = self._calculate_realized_pnl(position, closing_qty, exit_price)
                position.realized_pnl += realized_pnl
                position.quantity = position.quantity - (closing_qty if position.quantity > 0 else -closing_qty)
                self.daily_pnl += realized_pnl

                self.logger.info(f"Position PARTIALLY CLOSED: {symbol} - Closed: {closing_qty}, Remaining: {position.quantity}, P&L: ₹{realized_pnl:.2f}")

        except Exception as e:
            self.logger.error(f"Error closing position for {symbol}: {e}")

    def _calculate_realized_pnl(self, position: Position, closing_qty: int, exit_price: float) -> float:
        """
        Calculate realized P&L for closing trade

        Args:
            position: Position object
            closing_qty: Quantity being closed
            exit_price: Exit price

        Returns:
            Realized P&L
        """
        # P&L = (Exit Price - Entry Price) * Quantity
        # For short positions, reverse the calculation
        if position.quantity > 0:  # Long position
            pnl = (exit_price - position.avg_price) * closing_qty
        else:  # Short position
            pnl = (position.avg_price - exit_price) * closing_qty

        return pnl

    # =========================================================================
    # POSITION QUERIES
    # =========================================================================

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Position]:
        """Get all open positions"""
        return self.positions.copy()

    def has_position(self, symbol: str) -> bool:
        """Check if position exists for symbol"""
        return symbol in self.positions

    def get_position_count(self) -> int:
        """Get number of open positions"""
        return len(self.positions)

    # =========================================================================
    # P&L CALCULATIONS
    # =========================================================================

    def update_current_prices(self):
        """Update current prices for all open positions (DYNAMIC)"""
        try:
            if not self.positions:
                return

            symbols_list = [f"{symbol.split(':')[-1] if ':' in symbol else symbol}" for symbol in self.positions.keys()]
            exchange_symbols = [f"NFO:{symbol}" for symbol in symbols_list]

            # Fetch current prices
            ltps = self.kite.get_ltp(exchange_symbols)

            for symbol in self.positions:
                clean_symbol = symbol.split(':')[-1] if ':' in symbol else symbol
                full_symbol = f"NFO:{clean_symbol}"

                if full_symbol in ltps:
                    current_price = ltps[full_symbol].get('last_price', 0)
                    self.positions[symbol].current_price = current_price

                    # Calculate unrealized P&L
                    position = self.positions[symbol]
                    if position.quantity > 0:  # Long
                        position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                    else:  # Short
                        position.unrealized_pnl = (position.avg_price - current_price) * abs(position.quantity)

        except Exception as e:
            self.logger.error(f"Error updating current prices: {e}")

    def get_total_pnl(self) -> Dict[str, float]:
        """
        Get total P&L summary

        Returns:
            Dictionary with realized, unrealized, and total P&L
        """
        self.update_current_prices()

        realized = sum(p.realized_pnl for p in self.positions.values()) + \
                  sum(p.realized_pnl for p in self.closed_positions)

        unrealized = sum(p.unrealized_pnl for p in self.positions.values())

        return {
            'realized_pnl': realized,
            'unrealized_pnl': unrealized,
            'total_pnl': realized + unrealized,
            'daily_pnl': self.daily_pnl
        }

    def get_position_summary(self) -> List[Dict]:
        """
        Get summary of all positions

        Returns:
            List of position dictionaries
        """
        self.update_current_prices()

        summary = []
        for symbol, position in self.positions.items():
            summary.append({
                'symbol': symbol,
                'quantity': position.quantity,
                'avg_price': position.avg_price,
                'current_price': position.current_price,
                'unrealized_pnl': position.unrealized_pnl,
                'realized_pnl': position.realized_pnl,
                'entry_time': position.entry_time.strftime('%Y-%m-%d %H:%M:%S') if position.entry_time else None
            })

        return summary

    # =========================================================================
    # POSITION MANAGEMENT ACTIONS
    # =========================================================================

    def squareoff_position(self, symbol: str, order_manager) -> bool:
        """
        Square off a position (close completely)

        Args:
            symbol: Trading symbol
            order_manager: OrderManager instance for placing orders

        Returns:
            True if successful
        """
        try:
            if symbol not in self.positions:
                self.logger.warning(f"No position to square off for {symbol}")
                return False

            position = self.positions[symbol]

            # Determine transaction type (opposite of current position)
            transaction_type = 'SELL' if position.quantity > 0 else 'BUY'
            quantity_lots = abs(position.quantity) // LOT_SIZE

            self.logger.info(f"Squaring off position: {symbol} - {transaction_type} {quantity_lots} lots")

            # Place market order to exit
            order_id = order_manager.place_market_order(
                symbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity_lots,
                tag="SQUAREOFF"
            )

            if order_id:
                self.logger.info(f"Squareoff order placed: {order_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error squaring off position for {symbol}: {e}")
            return False

    def squareoff_all_positions(self, order_manager) -> Dict[str, bool]:
        """
        Square off all open positions

        Args:
            order_manager: OrderManager instance

        Returns:
            Dictionary of {symbol: success_status}
        """
        results = {}
        symbols = list(self.positions.keys())

        self.logger.warning(f"Squaring off ALL positions ({len(symbols)} positions)")

        for symbol in symbols:
            results[symbol] = self.squareoff_position(symbol, order_manager)

        return results

    # =========================================================================
    # STATISTICS & REPORTING
    # =========================================================================

    def get_trading_statistics(self) -> Dict:
        """
        Get trading statistics for the day

        Returns:
            Dictionary with trading stats
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        pnl = self.get_total_pnl()

        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'open_positions': len(self.positions),
            'daily_pnl': self.daily_pnl,
            'realized_pnl': pnl['realized_pnl'],
            'unrealized_pnl': pnl['unrealized_pnl'],
            'total_pnl': pnl['total_pnl']
        }

    def print_position_summary(self):
        """Print formatted position summary"""
        self.update_current_prices()

        print("\n" + "="*80)
        print("POSITION SUMMARY")
        print("="*80)

        if not self.positions:
            print("No open positions")
        else:
            for symbol, position in self.positions.items():
                print(f"\n{symbol}:")
                print(f"  Quantity: {position.quantity}")
                print(f"  Avg Price: ₹{position.avg_price:.2f}")
                print(f"  Current Price: ₹{position.current_price:.2f}")
                print(f"  Unrealized P&L: ₹{position.unrealized_pnl:.2f}")
                print(f"  Realized P&L: ₹{position.realized_pnl:.2f}")

        pnl = self.get_total_pnl()
        stats = self.get_trading_statistics()

        print("\n" + "-"*80)
        print(f"Daily P&L: ₹{pnl['daily_pnl']:.2f}")
        print(f"Unrealized P&L: ₹{pnl['unrealized_pnl']:.2f}")
        print(f"Total P&L: ₹{pnl['total_pnl']:.2f}")
        print(f"Trades: {stats['total_trades']} (W:{stats['winning_trades']} L:{stats['losing_trades']})")
        print(f"Win Rate: {stats['win_rate']:.1f}%")
        print("="*80 + "\n")


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Position Manager...")
    print("="*60)

    try:
        from src.api.kite_wrapper import KiteWrapper
        from src.data.market_data import MarketData

        kite = KiteWrapper()
        market_data = MarketData(kite)
        options_chain = OptionsChain(kite, market_data)
        position_manager = PositionManager(kite, options_chain, paper_trading=True)

        print("\n1. Testing Position Updates")
        position_manager.update_position("NIFTY24NOV24000CE", "BUY", 1, 150.0)
        position_manager.update_position("NIFTY24NOV24000PE", "SELL", 1, 140.0)

        print("\n2. Position Summary")
        position_manager.print_position_summary()

        print("\n3. Simulating Partial Close")
        position_manager.update_position("NIFTY24NOV24000CE", "SELL", 1, 160.0)

        print("\n4. Final Summary")
        position_manager.print_position_summary()

        stats = position_manager.get_trading_statistics()
        print(f"\nTrading Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n" + "="*60)
        print("✓ All tests completed!")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
