"""
Telegram Bot Module
Sends real-time notifications:
- Trade alerts (entry, exit, P&L)
- Risk alerts (SL hit, daily loss warning)
- System status updates
- Daily summary
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import requests

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.utils.logger import get_logger


class TelegramBot:
    """
    Telegram Bot for trading notifications
    """

    def __init__(self, bot_token: str = None, chat_id: str = None, enabled: bool = None):
        """
        Initialize Telegram Bot

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
            enabled: Enable/disable notifications
        """
        self.logger = get_logger(__name__)

        self.enabled = enabled if enabled is not None else TELEGRAM_ENABLED
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

        if self.enabled and (not self.bot_token or not self.chat_id):
            self.logger.warning("Telegram enabled but token/chat_id missing. Disabling.")
            self.enabled = False

        if self.enabled:
            self.logger.info("Telegram Bot initialized and ENABLED")
        else:
            self.logger.info("Telegram Bot DISABLED")

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send message via Telegram

        Args:
            message: Message text
            parse_mode: Parse mode (HTML or Markdown)

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False

    # Pre-formatted messages
    def send_trade_entry(self, symbol: str, transaction_type: str, quantity: int, price: float, strategy: str = None):
        """Send trade entry notification"""
        message = f"""
🔵 <b>TRADE ENTRY</b>
Symbol: {symbol}
Type: {transaction_type}
Quantity: {quantity}
Price: ₹{price:.2f}
Strategy: {strategy or 'N/A'}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        self.send_message(message)

    def send_trade_exit(self, symbol: str, pnl: float, exit_price: float):
        """Send trade exit notification"""
        emoji = "🟢" if pnl > 0 else "🔴"
        message = f"""
{emoji} <b>TRADE EXIT</b>
Symbol: {symbol}
Exit Price: ₹{exit_price:.2f}
P&L: ₹{pnl:.2f}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        self.send_message(message)

    def send_daily_summary(self, summary: dict):
        """Send daily summary"""
        message = f"""
📊 <b>DAILY SUMMARY</b>
Date: {datetime.now().strftime('%Y-%m-%d')}

Trades: {summary.get('total_trades', 0)}
Win Rate: {summary.get('win_rate', 0):.1f}%
Net P&L: ₹{summary.get('net_pnl', 0):.2f}

Winning: {summary.get('winning_trades', 0)}
Losing: {summary.get('losing_trades', 0)}
"""
        self.send_message(message)

    def send_risk_alert(self, alert_type: str, message: str):
        """Send risk alert"""
        msg = f"""
⚠️ <b>RISK ALERT</b>
Type: {alert_type}
{message}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        self.send_message(msg)


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Telegram Bot...")

    bot = TelegramBot(enabled=False)  # Disable for testing

    print("✓ Telegram Bot module loaded successfully")
    print("Note: Set TELEGRAM_ENABLED=true in config to enable notifications")
