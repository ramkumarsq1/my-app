"""
Order Execution Manager
Handles all order-related operations:
- Order placement with pre-checks
- Order modification and cancellation
- Order status tracking
- Retry logic for failed orders
- Stop-loss and target order management
- Paper trading mode support
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
from enum import Enum

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import (
    EXCHANGE, PRODUCT_TYPE, ORDER_TYPE_DEFAULT,
    LOT_SIZE, PAPER_TRADING, API_RETRY_COUNT
)
from src.utils.logger import get_logger
from src.api.kite_wrapper import KiteWrapper


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    PLACED = "PLACED"
    COMPLETE = "COMPLETE"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"  # Stop-Loss Limit
    SL_M = "SL-M"  # Stop-Loss Market


class TransactionType(Enum):
    """Transaction type enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderManager:
    """
    Order Execution Manager
    Handles all order operations with safety checks and error handling
    """

    def __init__(self, kite_wrapper: KiteWrapper, paper_trading: bool = None):
        """
        Initialize Order Manager

        Args:
            kite_wrapper: Initialized KiteWrapper instance
            paper_trading: Enable paper trading mode (overrides config if specified)
        """
        self.kite = kite_wrapper
        self.logger = get_logger(__name__)

        # Paper trading mode
        self.paper_trading = paper_trading if paper_trading is not None else PAPER_TRADING

        # Order tracking
        self.orders = {}  # order_id: order_details
        self.paper_order_id_counter = 1000  # For paper trading

        if self.paper_trading:
            self.logger.warning("="*60)
            self.logger.warning("PAPER TRADING MODE ENABLED - NO REAL ORDERS WILL BE PLACED")
            self.logger.warning("="*60)
        else:
            self.logger.info("LIVE TRADING MODE - Real orders will be placed")

        self.logger.info("OrderManager initialized")

    # =========================================================================
    # ORDER PLACEMENT
    # =========================================================================

    def place_market_order(self, symbol: str, transaction_type: str, quantity: int,
                          tag: str = None) -> Optional[str]:
        """
        Place a market order

        Args:
            symbol: Trading symbol
            transaction_type: 'BUY' or 'SELL'
            quantity: Quantity (in lots)
            tag: Optional tag for tracking

        Returns:
            Order ID or None if failed
        """
        try:
            # Validate inputs
            if quantity <= 0:
                self.logger.error("Quantity must be positive")
                return None

            # Convert lots to quantity
            total_quantity = quantity * LOT_SIZE

            self.logger.info(f"Placing MARKET order: {transaction_type} {quantity} lots ({total_quantity} qty) of {symbol}")

            if self.paper_trading:
                return self._place_paper_order(symbol, transaction_type, total_quantity, "MARKET", tag=tag)

            # Place real order
            order_id = self.kite.place_order(
                symbol=symbol,
                exchange=EXCHANGE,
                transaction_type=transaction_type.upper(),
                quantity=total_quantity,
                order_type="MARKET",
                product=PRODUCT_TYPE,
                tag=tag
            )

            # Track order
            self.orders[order_id] = {
                'order_id': order_id,
                'symbol': symbol,
                'transaction_type': transaction_type,
                'quantity': total_quantity,
                'order_type': 'MARKET',
                'status': OrderStatus.PLACED.value,
                'timestamp': datetime.now(),
                'tag': tag
            }

            self.logger.log_order(order_id, 'PLACED', self.orders[order_id])
            return order_id

        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            return None

    def place_limit_order(self, symbol: str, transaction_type: str, quantity: int,
                         price: float, tag: str = None) -> Optional[str]:
        """
        Place a limit order

        Args:
            symbol: Trading symbol
            transaction_type: 'BUY' or 'SELL'
            quantity: Quantity (in lots)
            price: Limit price
            tag: Optional tag for tracking

        Returns:
            Order ID or None if failed
        """
        try:
            if quantity <= 0:
                self.logger.error("Quantity must be positive")
                return None

            if price <= 0:
                self.logger.error("Price must be positive")
                return None

            total_quantity = quantity * LOT_SIZE

            self.logger.info(f"Placing LIMIT order: {transaction_type} {quantity} lots of {symbol} @ ₹{price}")

            if self.paper_trading:
                return self._place_paper_order(symbol, transaction_type, total_quantity, "LIMIT", price=price, tag=tag)

            # Place real order
            order_id = self.kite.place_order(
                symbol=symbol,
                exchange=EXCHANGE,
                transaction_type=transaction_type.upper(),
                quantity=total_quantity,
                order_type="LIMIT",
                price=price,
                product=PRODUCT_TYPE,
                tag=tag
            )

            # Track order
            self.orders[order_id] = {
                'order_id': order_id,
                'symbol': symbol,
                'transaction_type': transaction_type,
                'quantity': total_quantity,
                'order_type': 'LIMIT',
                'price': price,
                'status': OrderStatus.PLACED.value,
                'timestamp': datetime.now(),
                'tag': tag
            }

            self.logger.log_order(order_id, 'PLACED', self.orders[order_id])
            return order_id

        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            return None

    def place_sl_order(self, symbol: str, transaction_type: str, quantity: int,
                      trigger_price: float, price: float = None, tag: str = None) -> Optional[str]:
        """
        Place a stop-loss order

        Args:
            symbol: Trading symbol
            transaction_type: 'BUY' or 'SELL'
            quantity: Quantity (in lots)
            trigger_price: Trigger price
            price: Limit price (None for SL-M market order)
            tag: Optional tag for tracking

        Returns:
            Order ID or None if failed
        """
        try:
            if quantity <= 0:
                self.logger.error("Quantity must be positive")
                return None

            if trigger_price <= 0:
                self.logger.error("Trigger price must be positive")
                return None

            total_quantity = quantity * LOT_SIZE
            order_type = "SL" if price else "SL-M"

            self.logger.info(f"Placing {order_type} order: {transaction_type} {quantity} lots of {symbol} @ trigger ₹{trigger_price}")

            if self.paper_trading:
                return self._place_paper_order(
                    symbol, transaction_type, total_quantity, order_type,
                    price=price, trigger_price=trigger_price, tag=tag
                )

            # Place real order
            order_id = self.kite.place_order(
                symbol=symbol,
                exchange=EXCHANGE,
                transaction_type=transaction_type.upper(),
                quantity=total_quantity,
                order_type=order_type,
                price=price,
                trigger_price=trigger_price,
                product=PRODUCT_TYPE,
                tag=tag
            )

            # Track order
            self.orders[order_id] = {
                'order_id': order_id,
                'symbol': symbol,
                'transaction_type': transaction_type,
                'quantity': total_quantity,
                'order_type': order_type,
                'trigger_price': trigger_price,
                'price': price,
                'status': OrderStatus.PLACED.value,
                'timestamp': datetime.now(),
                'tag': tag
            }

            self.logger.log_order(order_id, 'PLACED', self.orders[order_id])
            return order_id

        except Exception as e:
            self.logger.error(f"Error placing stop-loss order: {e}")
            return None

    # =========================================================================
    # ORDER MODIFICATION & CANCELLATION
    # =========================================================================

    def modify_order(self, order_id: str, quantity: int = None, price: float = None,
                    trigger_price: float = None) -> bool:
        """
        Modify an existing order

        Args:
            order_id: Order ID to modify
            quantity: New quantity (in lots)
            price: New price
            trigger_price: New trigger price

        Returns:
            True if successful
        """
        try:
            if self.paper_trading:
                self.logger.info(f"[PAPER] Modifying order {order_id}")
                if order_id in self.orders:
                    if quantity:
                        self.orders[order_id]['quantity'] = quantity * LOT_SIZE
                    if price:
                        self.orders[order_id]['price'] = price
                    if trigger_price:
                        self.orders[order_id]['trigger_price'] = trigger_price
                return True

            # Modify real order
            modified_quantity = quantity * LOT_SIZE if quantity else None

            self.kite.modify_order(
                order_id=order_id,
                quantity=modified_quantity,
                price=price,
                trigger_price=trigger_price
            )

            # Update tracking
            if order_id in self.orders:
                if quantity:
                    self.orders[order_id]['quantity'] = modified_quantity
                if price:
                    self.orders[order_id]['price'] = price
                if trigger_price:
                    self.orders[order_id]['trigger_price'] = trigger_price

            self.logger.log_order(order_id, 'MODIFIED', {'qty': modified_quantity, 'price': price})
            return True

        except Exception as e:
            self.logger.error(f"Error modifying order {order_id}: {e}")
            return False

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Cancelling order: {order_id}")

            if self.paper_trading:
                if order_id in self.orders:
                    self.orders[order_id]['status'] = OrderStatus.CANCELLED.value
                    self.logger.log_order(order_id, 'CANCELLED', {})
                return True

            # Cancel real order
            self.kite.cancel_order(order_id=order_id)

            # Update tracking
            if order_id in self.orders:
                self.orders[order_id]['status'] = OrderStatus.CANCELLED.value

            self.logger.log_order(order_id, 'CANCELLED', {})
            return True

        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    # =========================================================================
    # ORDER STATUS & TRACKING
    # =========================================================================

    def get_order_status(self, order_id: str) -> Optional[str]:
        """
        Get current status of an order

        Args:
            order_id: Order ID

        Returns:
            Order status string or None
        """
        try:
            if self.paper_trading:
                return self.orders.get(order_id, {}).get('status')

            # Get status from broker
            history = self.kite.get_order_history(order_id)
            if history:
                latest = history[-1]  # Get latest status
                status = latest.get('status', 'UNKNOWN')

                # Update tracking
                if order_id in self.orders:
                    self.orders[order_id]['status'] = status

                return status

            return None

        except Exception as e:
            self.logger.error(f"Error getting order status for {order_id}: {e}")
            return None

    def wait_for_order_completion(self, order_id: str, timeout: int = 30) -> bool:
        """
        Wait for order to complete

        Args:
            order_id: Order ID
            timeout: Maximum wait time in seconds

        Returns:
            True if order completed successfully
        """
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                status = self.get_order_status(order_id)

                if status == 'COMPLETE':
                    self.logger.info(f"Order {order_id} completed successfully")
                    return True

                if status in ['REJECTED', 'CANCELLED']:
                    self.logger.error(f"Order {order_id} failed with status: {status}")
                    return False

                time.sleep(1)  # Check every second

            self.logger.warning(f"Order {order_id} completion timeout")
            return False

        except Exception as e:
            self.logger.error(f"Error waiting for order completion: {e}")
            return False

    def get_all_orders_today(self) -> List[Dict]:
        """
        Get all orders placed today

        Returns:
            List of order dictionaries
        """
        try:
            if self.paper_trading:
                return list(self.orders.values())

            orders = self.kite.get_orders()
            return orders

        except Exception as e:
            self.logger.error(f"Error getting today's orders: {e}")
            return []

    # =========================================================================
    # BRACKET ORDERS (ENTRY + SL + TARGET)
    # =========================================================================

    def place_bracket_order(self, symbol: str, transaction_type: str, quantity: int,
                           entry_price: float, stop_loss: float, target: float,
                           tag: str = None) -> Dict:
        """
        Place a bracket order (entry + stop-loss + target)

        Args:
            symbol: Trading symbol
            transaction_type: 'BUY' or 'SELL'
            quantity: Quantity in lots
            entry_price: Entry price (0 for market order)
            stop_loss: Stop-loss price
            target: Target price
            tag: Optional tag

        Returns:
            Dictionary with order IDs {'entry': id, 'sl': id, 'target': id}
        """
        try:
            result = {'entry': None, 'sl': None, 'target': None}

            # Place entry order
            if entry_price == 0:
                entry_order_id = self.place_market_order(symbol, transaction_type, quantity, tag=f"{tag}_ENTRY" if tag else "ENTRY")
            else:
                entry_order_id = self.place_limit_order(symbol, transaction_type, quantity, entry_price, tag=f"{tag}_ENTRY" if tag else "ENTRY")

            if not entry_order_id:
                self.logger.error("Failed to place entry order")
                return result

            result['entry'] = entry_order_id

            # Wait for entry order completion
            if not self.wait_for_order_completion(entry_order_id, timeout=10):
                self.logger.warning("Entry order not completed, cancelling...")
                self.cancel_order(entry_order_id)
                return result

            # Place SL order (opposite side)
            sl_transaction = 'SELL' if transaction_type == 'BUY' else 'BUY'
            sl_order_id = self.place_sl_order(symbol, sl_transaction, quantity, stop_loss, tag=f"{tag}_SL" if tag else "SL")
            result['sl'] = sl_order_id

            # Place target order (opposite side, limit order)
            target_order_id = self.place_limit_order(symbol, sl_transaction, quantity, target, tag=f"{tag}_TARGET" if tag else "TARGET")
            result['target'] = target_order_id

            self.logger.info(f"Bracket order placed: Entry={entry_order_id}, SL={sl_order_id}, Target={target_order_id}")
            return result

        except Exception as e:
            self.logger.error(f"Error placing bracket order: {e}")
            return result

    # =========================================================================
    # PAPER TRADING
    # =========================================================================

    def _place_paper_order(self, symbol: str, transaction_type: str, quantity: int,
                          order_type: str, price: float = None, trigger_price: float = None,
                          tag: str = None) -> str:
        """
        Simulate order placement in paper trading mode

        Returns:
            Simulated order ID
        """
        order_id = f"PAPER_{self.paper_order_id_counter}"
        self.paper_order_id_counter += 1

        self.orders[order_id] = {
            'order_id': order_id,
            'symbol': symbol,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'order_type': order_type,
            'price': price,
            'trigger_price': trigger_price,
            'status': OrderStatus.COMPLETE.value,  # Auto-complete in paper trading
            'timestamp': datetime.now(),
            'tag': tag,
            'paper_trading': True
        }

        self.logger.info(f"[PAPER] Order placed: {order_id} - {transaction_type} {quantity} {symbol}")
        return order_id

    def enable_live_trading(self):
        """Enable live trading mode (WARNING: Use with caution!)"""
        self.logger.critical("="*60)
        self.logger.critical("SWITCHING TO LIVE TRADING MODE!")
        self.logger.critical("Real money will be at risk!")
        self.logger.critical("="*60)
        self.paper_trading = False

    def enable_paper_trading(self):
        """Enable paper trading mode (safe mode)"""
        self.logger.info("Switching to PAPER TRADING MODE (safe mode)")
        self.paper_trading = True


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Order Manager...")
    print("="*60)

    try:
        from src.api.kite_wrapper import KiteWrapper
        from config.config import KITE_ACCESS_TOKEN

        if not KITE_ACCESS_TOKEN:
            print("⚠ No access token found. Testing in paper trading mode.")

        kite = KiteWrapper()
        order_manager = OrderManager(kite, paper_trading=True)  # Always use paper trading for tests

        print("\n1. Testing Market Order (Paper)")
        order_id = order_manager.place_market_order("NIFTY24NOV24000CE", "BUY", 1, tag="TEST")
        print(f"   Order ID: {order_id}")

        print("\n2. Testing Limit Order (Paper)")
        order_id = order_manager.place_limit_order("NIFTY24NOV24000PE", "SELL", 1, 150.0, tag="TEST")
        print(f"   Order ID: {order_id}")

        print("\n3. Testing Stop-Loss Order (Paper)")
        order_id = order_manager.place_sl_order("NIFTY24NOV24000CE", "SELL", 1, 100.0, tag="TEST_SL")
        print(f"   Order ID: {order_id}")

        print("\n4. Testing Order Status")
        if order_id:
            status = order_manager.get_order_status(order_id)
            print(f"   Status: {status}")

        print("\n5. Testing All Orders")
        all_orders = order_manager.get_all_orders_today()
        print(f"   Total orders: {len(all_orders)}")

        print("\n" + "="*60)
        print("✓ All tests completed!")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
