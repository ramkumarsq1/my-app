"""
Nifty Options Trading Platform - Main Entry Point
Automated trading system for NSE Nifty weekly options

SAFETY FIRST:
- Always start with PAPER_TRADING = True
- Test thoroughly before going live
- Monitor positions continuously
- Respect risk limits
"""

import sys
from pathlib import Path
import time
from datetime import datetime
import signal

# Add src to path
sys.path.append(str(Path(__file__).parent))

from config.config import (
    PAPER_TRADING, KITE_ACCESS_TOKEN,
    print_config, validate_config
)
from src.utils.logger import get_logger
from src.api.kite_wrapper import KiteWrapper
from src.data.market_data import MarketData
from src.data.options_chain import OptionsChain
from src.execution.order_manager import OrderManager
from src.execution.position_manager import PositionManager
from src.risk.risk_manager import RiskManager
from src.database.database import TradingDatabase
from src.notifications.telegram_bot import TelegramBot
from src.strategies.sample_strategy import ATMStraddleStrategy


class TradingEngine:
    """
    Main Trading Engine
    Coordinates all components and runs the trading loop
    """

    def __init__(self):
        """Initialize trading engine"""
        self.logger = get_logger("TradingEngine")
        self.running = False

        self.logger.info("="*80)
        self.logger.info("NIFTY OPTIONS TRADING PLATFORM")
        self.logger.info("="*80)

        # Validate configuration
        validation = validate_config()
        if not validation['api_credentials']:
            self.logger.error("API credentials not configured. Please set them in config.")
            raise ValueError("Missing API credentials")

        # Print configuration
        print_config(masked=True)

        # Initialize components
        self.logger.info("Initializing components...")

        self.kite = KiteWrapper()
        self.market_data = MarketData(self.kite)
        self.options_chain = OptionsChain(self.kite, self.market_data)
        self.order_manager = OrderManager(self.kite, paper_trading=PAPER_TRADING)
        self.position_manager = PositionManager(self.kite, self.options_chain, paper_trading=PAPER_TRADING)
        self.risk_manager = RiskManager(self.kite)
        self.database = TradingDatabase()
        self.telegram = TelegramBot()

        # Initialize strategy
        self.strategy = ATMStraddleStrategy()

        self.logger.info("✓ All components initialized successfully")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def start(self):
        """Start the trading engine"""
        try:
            self.logger.info("="*80)
            self.logger.info("STARTING TRADING ENGINE")
            self.logger.info("="*80)

            # Reset daily stats
            self.risk_manager.reset_daily_stats()

            # Check market status
            self._check_market_status()

            # Start main loop
            self.running = True
            self._main_loop()

        except KeyboardInterrupt:
            self.logger.info("Shutdown requested by user")
            self.shutdown()

        except Exception as e:
            self.logger.critical(f"Fatal error in trading engine: {e}", exc_info=True)
            self.shutdown()

    def _main_loop(self):
        """Main trading loop"""
        self.logger.info("Entering main trading loop...")

        loop_count = 0

        while self.running:
            try:
                loop_count += 1

                # Check if market is open
                if not self.market_data.is_market_open():
                    self.logger.info("Market is closed. Waiting...")
                    time.sleep(60)
                    continue

                # Check if trading is allowed
                if not self.market_data.is_trading_allowed():
                    self.logger.debug("Outside trading hours")
                    time.sleep(30)
                    continue

                # Check force exit condition
                if self.market_data.should_force_exit():
                    self.logger.warning("Force exit time reached!")
                    self._force_exit_all_positions()
                    break

                # Update positions and check risk
                self._update_positions()

                # Generate and execute trading signals
                if self.strategy.is_enabled():
                    self._process_strategy_signals()

                # Check exit conditions for open positions
                self._check_exit_conditions()

                # Log status every 10 loops (~5 minutes)
                if loop_count % 10 == 0:
                    self._log_status()

                # Sleep between iterations
                time.sleep(30)  # 30 seconds

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)

    def _check_market_status(self):
        """Check and log market status"""
        try:
            status = self.market_data.get_market_status_summary()

            self.logger.info("\nMarket Status:")
            self.logger.info(f"  Nifty Spot: {status.get('nifty_spot', 0):,.2f}")
            self.logger.info(f"  ATM Strike: {status.get('atm_strike', 0)}")
            self.logger.info(f"  Market Open: {status.get('market_open', False)}")
            self.logger.info(f"  Trading Allowed: {status.get('trading_allowed', False)}")
            self.logger.info(f"  Minutes to Close: {status.get('minutes_to_close', 0)}")

            if not status.get('market_open'):
                self.logger.warning("Market is currently CLOSED")

        except Exception as e:
            self.logger.error(f"Error checking market status: {e}")

    def _update_positions(self):
        """Update current positions and P&L"""
        try:
            self.position_manager.update_current_prices()

            # Get P&L summary
            pnl = self.position_manager.get_total_pnl()
            self.risk_manager.daily_pnl = pnl.get('daily_pnl', 0)

            # Check risk levels
            risk_summary = self.risk_manager.get_risk_summary()

            if risk_summary['risk_level'] == 'CRITICAL':
                self.logger.critical(f"CRITICAL RISK LEVEL - Daily P&L: ₹{self.risk_manager.daily_pnl:.2f}")
                self.telegram.send_risk_alert("CRITICAL", f"Daily P&L: ₹{self.risk_manager.daily_pnl:.2f}")

        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")

    def _process_strategy_signals(self):
        """Process strategy signals"""
        try:
            # Get current market data
            spot = self.market_data.get_nifty_spot_price()
            atm = self.market_data.calculate_atm_strike(spot)

            # Get ATM option prices
            ce_ltp = self.options_chain.get_option_ltp(atm, 'CE')
            pe_ltp = self.options_chain.get_option_ltp(atm, 'PE')

            market_data = {
                'spot_price': spot,
                'atm_strike': atm,
                'atm_ce_price': ce_ltp,
                'atm_pe_price': pe_ltp
            }

            # Generate signal
            signal = self.strategy.generate_signal(market_data)

            if signal and signal.get('action') == 'ENTRY':
                self._execute_entry_signal(signal)

        except Exception as e:
            self.logger.error(f"Error processing strategy signals: {e}")

    def _execute_entry_signal(self, signal: dict):
        """Execute entry signal"""
        try:
            self.logger.info(f"Entry signal received: {signal.get('strategy')}")

            # Check risk before entry
            total_premium = signal.get('total_premium', 0)
            quantity = signal.get('legs', [{}])[0].get('quantity', 1)

            risk_ok, risk_reason = self.risk_manager.check_pre_trade_risk(
                symbol="STRADDLE",
                quantity=quantity,
                estimated_price=total_premium,
                transaction_type="BUY",
                position_manager=self.position_manager
            )

            if not risk_ok:
                self.logger.warning(f"Entry blocked by risk manager: {risk_reason}")
                return

            # Execute each leg
            for leg in signal.get('legs', []):
                strike = leg.get('strike')
                option_type = leg.get('symbol_type')
                symbol = self.options_chain.generate_option_symbol(strike, option_type)

                order_id = self.order_manager.place_market_order(
                    symbol=symbol,
                    transaction_type=leg.get('transaction_type'),
                    quantity=leg.get('quantity'),
                    tag=signal.get('strategy')
                )

                if order_id:
                    self.logger.info(f"Order placed: {order_id} for {symbol}")
                    self.telegram.send_trade_entry(
                        symbol, leg.get('transaction_type'),
                        leg.get('quantity'), leg.get('price'),
                        signal.get('strategy')
                    )

                    # Update position
                    self.position_manager.update_position(
                        symbol, leg.get('transaction_type'),
                        leg.get('quantity'), leg.get('price')
                    )

        except Exception as e:
            self.logger.error(f"Error executing entry signal: {e}")

    def _check_exit_conditions(self):
        """Check exit conditions for open positions"""
        try:
            positions = self.position_manager.get_all_positions()

            for symbol, position in positions.items():
                # Get current price
                current_price = position.current_price

                # Check strategy exit
                should_exit, reason = self.strategy.should_exit(
                    {'avg_price': position.avg_price},
                    current_price
                )

                if should_exit:
                    self.logger.info(f"Exit signal for {symbol}: {reason}")
                    self._execute_exit(symbol, reason)

        except Exception as e:
            self.logger.error(f"Error checking exit conditions: {e}")

    def _execute_exit(self, symbol: str, reason: str):
        """Execute position exit"""
        try:
            success = self.position_manager.squareoff_position(symbol, self.order_manager)

            if success:
                self.logger.info(f"Position squared off: {symbol} - Reason: {reason}")
                self.telegram.send_trade_exit(symbol, 0, 0)  # Update with actual P&L

        except Exception as e:
            self.logger.error(f"Error executing exit: {e}")

    def _force_exit_all_positions(self):
        """Force exit all positions (EOD)"""
        try:
            self.logger.critical("FORCE EXITING ALL POSITIONS!")

            results = self.position_manager.squareoff_all_positions(self.order_manager)

            for symbol, success in results.items():
                status = "SUCCESS" if success else "FAILED"
                self.logger.info(f"Force exit {symbol}: {status}")

            self.telegram.send_risk_alert("FORCE EXIT", "All positions squared off (EOD)")

        except Exception as e:
            self.logger.error(f"Error in force exit: {e}")

    def _log_status(self):
        """Log current status"""
        try:
            stats = self.position_manager.get_trading_statistics()
            risk = self.risk_manager.get_risk_summary()

            self.logger.info("\n" + "="*60)
            self.logger.info("STATUS UPDATE")
            self.logger.info("-"*60)
            self.logger.info(f"Open Positions: {stats.get('open_positions', 0)}")
            self.logger.info(f"Daily P&L: ₹{stats.get('daily_pnl', 0):.2f}")
            self.logger.info(f"Total Trades: {stats.get('total_trades', 0)}")
            self.logger.info(f"Win Rate: {stats.get('win_rate', 0):.1f}%")
            self.logger.info(f"Risk Level: {risk.get('risk_level')}")
            self.logger.info("="*60 + "\n")

        except Exception as e:
            self.logger.error(f"Error logging status: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}. Initiating shutdown...")
        self.shutdown()

    def shutdown(self):
        """Shutdown trading engine gracefully"""
        self.logger.info("="*80)
        self.logger.info("SHUTTING DOWN TRADING ENGINE")
        self.logger.info("="*80)

        self.running = False

        # Save daily summary
        try:
            stats = self.position_manager.get_trading_statistics()
            today = datetime.now().strftime('%Y-%m-%d')
            self.database.save_daily_summary(today, stats)

            # Send summary
            self.telegram.send_daily_summary(stats)

        except Exception as e:
            self.logger.error(f"Error saving daily summary: {e}")

        # Close database
        self.database.close()

        self.logger.info("Shutdown complete. Goodbye!")
        sys.exit(0)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """Main entry point"""
    try:
        if not KITE_ACCESS_TOKEN:
            print("\n" + "="*80)
            print("ERROR: No access token found!")
            print("="*80)
            print("\nPlease set your Kite access token in one of the following ways:")
            print("1. Set KITE_ACCESS_TOKEN environment variable")
            print("2. Add it to config/config.ini")
            print("3. Generate it using the Kite login flow")
            print("\nRefer to README.md for detailed instructions.")
            print("="*80 + "\n")
            return

        # Create and start trading engine
        engine = TradingEngine()
        engine.start()

    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
