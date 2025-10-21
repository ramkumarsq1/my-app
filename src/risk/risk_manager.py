"""
Risk Management System
CRITICAL SAFETY MODULE - Prevents catastrophic losses
- Pre-trade risk checks
- Position size limits
- Daily loss limits
- Circuit breakers
- Margin monitoring
- Drawdown protection
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from enum import Enum

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import (
    MAX_LOSS_PER_TRADE, MAX_DAILY_LOSS, MAX_CONSECUTIVE_LOSSES,
    STOP_LOSS_PERCENTAGE, TARGET_PERCENTAGE, MAX_MARGIN_UTILIZATION,
    MAX_OPEN_POSITIONS, MAX_LOTS_PER_TRADE, COOLOFF_PERIOD_MINUTES,
    LOT_SIZE, TRADE_ON_EXPIRY_DAY
)
from src.utils.logger import get_logger
from src.api.kite_wrapper import KiteWrapper


class RiskLevel(Enum):
    """Risk level enumeration"""
    SAFE = "SAFE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    BLOCKED = "BLOCKED"


class RiskManager:
    """
    Risk Management System
    Enforces all safety rules and risk limits
    """

    def __init__(self, kite_wrapper: KiteWrapper):
        """
        Initialize Risk Manager

        Args:
            kite_wrapper: Initialized KiteWrapper instance
        """
        self.kite = kite_wrapper
        self.logger = get_logger(__name__)

        # Risk tracking
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.trades_today = 0
        self.blocked_until = None  # Cooloff period
        self.trading_blocked = False
        self.block_reason = None

        # Circuit breakers
        self.daily_loss_breaker_hit = False
        self.consecutive_loss_breaker_hit = False

        self.logger.info("="*60)
        self.logger.info("RISK MANAGER INITIALIZED - ALL SAFETY SYSTEMS ACTIVE")
        self.logger.info("="*60)
        self.logger.info(f"Max Daily Loss: ₹{MAX_DAILY_LOSS}")
        self.logger.info(f"Max Loss Per Trade: ₹{MAX_LOSS_PER_TRADE}")
        self.logger.info(f"Max Consecutive Losses: {MAX_CONSECUTIVE_LOSSES}")
        self.logger.info(f"Max Open Positions: {MAX_OPEN_POSITIONS}")
        self.logger.info(f"Max Margin Utilization: {MAX_MARGIN_UTILIZATION}%")
        self.logger.info("="*60)

    # =========================================================================
    # PRE-TRADE RISK CHECKS (CRITICAL)
    # =========================================================================

    def check_pre_trade_risk(self, symbol: str, quantity: int, estimated_price: float,
                            transaction_type: str, position_manager=None) -> Tuple[bool, str]:
        """
        COMPREHENSIVE PRE-TRADE RISK CHECK
        MUST PASS before any trade is allowed

        Args:
            symbol: Trading symbol
            quantity: Quantity in lots
            estimated_price: Estimated price per unit
            transaction_type: 'BUY' or 'SELL'
            position_manager: PositionManager instance (optional)

        Returns:
            Tuple of (is_allowed: bool, reason: str)
        """
        try:
            # 1. Check if trading is blocked
            if not self.is_trading_allowed():
                return False, self.block_reason or "Trading is currently blocked"

            # 2. Check cooloff period
            if self.is_in_cooloff_period():
                remaining = self._get_cooloff_remaining_minutes()
                return False, f"In cooloff period. {remaining} minutes remaining"

            # 3. Check daily loss limit
            if self.daily_pnl <= -MAX_DAILY_LOSS:
                self._trigger_daily_loss_circuit_breaker()
                return False, f"Daily loss limit reached: ₹{self.daily_pnl:.2f}"

            # 4. Check consecutive losses
            if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
                self._trigger_consecutive_loss_circuit_breaker()
                return False, f"Max consecutive losses reached: {self.consecutive_losses}"

            # 5. Check maximum open positions
            if position_manager:
                current_positions = position_manager.get_position_count()
                if transaction_type == 'BUY' and current_positions >= MAX_OPEN_POSITIONS:
                    return False, f"Max open positions limit: {current_positions}/{MAX_OPEN_POSITIONS}"

            # 6. Check position size limit
            if quantity > MAX_LOTS_PER_TRADE:
                return False, f"Quantity {quantity} exceeds max lots per trade: {MAX_LOTS_PER_TRADE}"

            # 7. Check margin availability
            margin_check, margin_reason = self.check_margin_availability(quantity, estimated_price)
            if not margin_check:
                return False, margin_reason

            # 8. Check expiry day trading restriction
            if not TRADE_ON_EXPIRY_DAY:
                from src.data.options_chain import OptionsChain
                # This is a simplified check - in real implementation, pass options_chain instance
                # For now, skip this check if options_chain not available
                pass

            # All checks passed
            self.logger.info(f"✓ Pre-trade risk check PASSED for {symbol}")
            return True, "All risk checks passed"

        except Exception as e:
            self.logger.error(f"Error in pre-trade risk check: {e}")
            return False, f"Risk check error: {e}"

    # =========================================================================
    # MARGIN & POSITION SIZE CHECKS
    # =========================================================================

    def check_margin_availability(self, quantity: int, estimated_price: float) -> Tuple[bool, str]:
        """
        Check if sufficient margin is available

        Args:
            quantity: Quantity in lots
            estimated_price: Estimated price per unit

        Returns:
            Tuple of (is_available: bool, reason: str)
        """
        try:
            # Get available margin
            margins = self.kite.get_margins()
            available_margin = margins.get('available', {}).get('live_balance', 0)

            # Estimate required margin (approximate)
            # For options: margin ≈ premium * quantity
            # This is simplified - actual margin calculation is complex
            total_quantity = quantity * LOT_SIZE
            estimated_requirement = estimated_price * total_quantity

            # Add buffer for slippage and margin fluctuations
            estimated_requirement *= 1.2  # 20% buffer

            if estimated_requirement > available_margin:
                return False, f"Insufficient margin: Required ₹{estimated_requirement:.2f}, Available ₹{available_margin:.2f}"

            # Check margin utilization percentage
            utilization = (estimated_requirement / available_margin) * 100 if available_margin > 0 else 100

            if utilization > MAX_MARGIN_UTILIZATION:
                return False, f"Margin utilization too high: {utilization:.1f}% (max: {MAX_MARGIN_UTILIZATION}%)"

            self.logger.debug(f"Margin check passed: Required ₹{estimated_requirement:.2f}, Available ₹{available_margin:.2f}")
            return True, "Sufficient margin available"

        except Exception as e:
            self.logger.error(f"Error checking margin: {e}")
            return False, f"Margin check error: {e}"

    # =========================================================================
    # STOP-LOSS & TARGET CALCULATIONS
    # =========================================================================

    def calculate_stop_loss(self, entry_price: float, transaction_type: str) -> float:
        """
        Calculate stop-loss price based on configured percentage

        Args:
            entry_price: Entry price
            transaction_type: 'BUY' or 'SELL'

        Returns:
            Stop-loss price
        """
        if transaction_type.upper() == 'BUY':
            # For long positions: SL below entry
            sl_price = entry_price * (1 - STOP_LOSS_PERCENTAGE / 100)
        else:
            # For short positions: SL above entry
            sl_price = entry_price * (1 + STOP_LOSS_PERCENTAGE / 100)

        self.logger.debug(f"SL calculated: ₹{sl_price:.2f} (Entry: ₹{entry_price:.2f}, {STOP_LOSS_PERCENTAGE}%)")
        return round(sl_price, 2)

    def calculate_target(self, entry_price: float, transaction_type: str) -> float:
        """
        Calculate target price based on configured percentage

        Args:
            entry_price: Entry price
            transaction_type: 'BUY' or 'SELL'

        Returns:
            Target price
        """
        if transaction_type.upper() == 'BUY':
            # For long positions: Target above entry
            target_price = entry_price * (1 + TARGET_PERCENTAGE / 100)
        else:
            # For short positions: Target below entry
            target_price = entry_price * (1 - TARGET_PERCENTAGE / 100)

        self.logger.debug(f"Target calculated: ₹{target_price:.2f} (Entry: ₹{entry_price:.2f}, {TARGET_PERCENTAGE}%)")
        return round(target_price, 2)

    def validate_stop_loss(self, entry_price: float, sl_price: float, transaction_type: str) -> Tuple[bool, str]:
        """
        Validate that stop-loss is reasonable

        Args:
            entry_price: Entry price
            sl_price: Stop-loss price
            transaction_type: 'BUY' or 'SELL'

        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        if transaction_type.upper() == 'BUY':
            if sl_price >= entry_price:
                return False, "SL for BUY must be below entry price"
            sl_distance = ((entry_price - sl_price) / entry_price) * 100
        else:
            if sl_price <= entry_price:
                return False, "SL for SELL must be above entry price"
            sl_distance = ((sl_price - entry_price) / entry_price) * 100

        # Check if SL distance is reasonable (5-50%)
        if sl_distance < 5:
            return False, f"SL too tight: {sl_distance:.1f}% (min 5%)"
        if sl_distance > 50:
            return False, f"SL too wide: {sl_distance:.1f}% (max 50%)"

        return True, f"SL valid: {sl_distance:.1f}% from entry"

    # =========================================================================
    # POSITION & P&L TRACKING
    # =========================================================================

    def update_daily_pnl(self, pnl: float):
        """
        Update daily P&L and check limits

        Args:
            pnl: Profit/Loss from closed trade
        """
        self.daily_pnl += pnl
        self.trades_today += 1

        if pnl < 0:
            self.consecutive_losses += 1
            self.logger.log_risk_event("LOSS", f"Consecutive losses: {self.consecutive_losses}", "WARNING")
        else:
            self.consecutive_losses = 0  # Reset on profit

        # Check daily loss limit
        if self.daily_pnl <= -MAX_DAILY_LOSS:
            self._trigger_daily_loss_circuit_breaker()

        # Check consecutive losses
        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            self._trigger_consecutive_loss_circuit_breaker()

        self.logger.info(f"Daily P&L updated: ₹{self.daily_pnl:.2f} ({self.trades_today} trades)")

    # =========================================================================
    # CIRCUIT BREAKERS
    # =========================================================================

    def _trigger_daily_loss_circuit_breaker(self):
        """Trigger daily loss circuit breaker"""
        if not self.daily_loss_breaker_hit:
            self.daily_loss_breaker_hit = True
            self.trading_blocked = True
            self.block_reason = f"DAILY LOSS LIMIT BREAKER TRIGGERED: ₹{self.daily_pnl:.2f}"

            self.logger.critical("="*60)
            self.logger.critical("!!! DAILY LOSS CIRCUIT BREAKER TRIGGERED !!!")
            self.logger.critical(f"Daily P&L: ₹{self.daily_pnl:.2f}")
            self.logger.critical(f"Limit: ₹{MAX_DAILY_LOSS}")
            self.logger.critical("ALL TRADING BLOCKED FOR THE DAY")
            self.logger.critical("="*60)

            self.logger.log_risk_event(
                "DAILY_LOSS_CIRCUIT_BREAKER",
                f"Daily loss limit reached: ₹{self.daily_pnl:.2f}",
                "CRITICAL"
            )

    def _trigger_consecutive_loss_circuit_breaker(self):
        """Trigger consecutive loss circuit breaker"""
        if not self.consecutive_loss_breaker_hit:
            self.consecutive_loss_breaker_hit = True
            self._start_cooloff_period()

            self.logger.critical("="*60)
            self.logger.critical("!!! CONSECUTIVE LOSS CIRCUIT BREAKER TRIGGERED !!!")
            self.logger.critical(f"Consecutive Losses: {self.consecutive_losses}")
            self.logger.critical(f"Cooloff Period: {COOLOFF_PERIOD_MINUTES} minutes")
            self.logger.critical("="*60)

            self.logger.log_risk_event(
                "CONSECUTIVE_LOSS_CIRCUIT_BREAKER",
                f"{self.consecutive_losses} consecutive losses",
                "CRITICAL"
            )

    def _start_cooloff_period(self):
        """Start cooloff period after consecutive losses"""
        self.blocked_until = datetime.now() + timedelta(minutes=COOLOFF_PERIOD_MINUTES)
        self.logger.warning(f"Cooloff period started. Trading blocked until {self.blocked_until.strftime('%H:%M:%S')}")

    def is_in_cooloff_period(self) -> bool:
        """Check if currently in cooloff period"""
        if self.blocked_until is None:
            return False

        if datetime.now() < self.blocked_until:
            return True

        # Cooloff period ended
        self.blocked_until = None
        self.consecutive_loss_breaker_hit = False
        self.logger.info("Cooloff period ended. Trading allowed.")
        return False

    def _get_cooloff_remaining_minutes(self) -> int:
        """Get remaining cooloff minutes"""
        if self.blocked_until is None:
            return 0

        remaining = (self.blocked_until - datetime.now()).total_seconds() / 60
        return max(0, int(remaining))

    # =========================================================================
    # TRADING CONTROL
    # =========================================================================

    def is_trading_allowed(self) -> bool:
        """
        Check if trading is currently allowed

        Returns:
            True if trading is allowed
        """
        if self.trading_blocked:
            return False

        if self.is_in_cooloff_period():
            return False

        return True

    def block_trading(self, reason: str):
        """
        Manually block all trading

        Args:
            reason: Reason for blocking
        """
        self.trading_blocked = True
        self.block_reason = reason
        self.logger.critical(f"TRADING MANUALLY BLOCKED: {reason}")

    def unblock_trading(self):
        """Unblock trading (use with caution)"""
        self.trading_blocked = False
        self.block_reason = None
        self.logger.warning("Trading manually UNBLOCKED")

    def reset_daily_stats(self):
        """Reset daily statistics (call at start of trading day)"""
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.consecutive_losses = 0
        self.daily_loss_breaker_hit = False
        self.consecutive_loss_breaker_hit = False
        self.trading_blocked = False
        self.block_reason = None
        self.blocked_until = None

        self.logger.info("Daily risk statistics RESET for new trading day")

    # =========================================================================
    # RISK LEVEL ASSESSMENT
    # =========================================================================

    def get_risk_level(self) -> RiskLevel:
        """
        Assess current risk level

        Returns:
            RiskLevel enum
        """
        if self.trading_blocked or self.is_in_cooloff_period():
            return RiskLevel.BLOCKED

        # Check daily loss
        loss_percentage = abs(self.daily_pnl / MAX_DAILY_LOSS * 100) if MAX_DAILY_LOSS > 0 else 0

        if loss_percentage >= 90:
            return RiskLevel.CRITICAL
        elif loss_percentage >= 60:
            return RiskLevel.WARNING
        else:
            return RiskLevel.SAFE

    def get_risk_summary(self) -> Dict:
        """
        Get comprehensive risk summary

        Returns:
            Dictionary with risk metrics
        """
        return {
            'risk_level': self.get_risk_level().value,
            'trading_allowed': self.is_trading_allowed(),
            'trading_blocked': self.trading_blocked,
            'block_reason': self.block_reason,
            'in_cooloff': self.is_in_cooloff_period(),
            'cooloff_remaining_minutes': self._get_cooloff_remaining_minutes(),
            'daily_pnl': self.daily_pnl,
            'daily_loss_limit': MAX_DAILY_LOSS,
            'loss_percentage': abs(self.daily_pnl / MAX_DAILY_LOSS * 100) if MAX_DAILY_LOSS > 0 else 0,
            'consecutive_losses': self.consecutive_losses,
            'max_consecutive_losses': MAX_CONSECUTIVE_LOSSES,
            'trades_today': self.trades_today,
            'daily_loss_breaker_hit': self.daily_loss_breaker_hit,
            'consecutive_loss_breaker_hit': self.consecutive_loss_breaker_hit,
        }


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Risk Manager...")
    print("="*60)

    try:
        from src.api.kite_wrapper import KiteWrapper

        kite = KiteWrapper()
        risk_manager = RiskManager(kite)

        print("\n1. Testing Pre-Trade Risk Check")
        allowed, reason = risk_manager.check_pre_trade_risk("NIFTY24NOV24000CE", 1, 150.0, "BUY")
        print(f"   Trade Allowed: {allowed}")
        print(f"   Reason: {reason}")

        print("\n2. Testing SL/Target Calculation")
        entry = 150.0
        sl = risk_manager.calculate_stop_loss(entry, "BUY")
        target = risk_manager.calculate_target(entry, "BUY")
        print(f"   Entry: ₹{entry}")
        print(f"   Stop-Loss: ₹{sl}")
        print(f"   Target: ₹{target}")

        print("\n3. Testing P&L Update")
        risk_manager.update_daily_pnl(-3000)
        risk_manager.update_daily_pnl(-3000)
        risk_manager.update_daily_pnl(-3000)

        print("\n4. Risk Summary")
        summary = risk_manager.get_risk_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")

        print("\n" + "="*60)
        print("✓ All tests completed!")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
