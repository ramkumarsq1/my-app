"""
Database Module
Handles all data persistence:
- Trade logging (all entries, exits, P&L)
- Order history
- Daily summary statistics
- Performance metrics
"""

import sys
from pathlib import Path
from datetime import datetime
import sqlite3
from typing import Dict, List, Optional
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config import DATABASE_PATH
from src.utils.logger import get_logger


class TradingDatabase:
    """
    Trading Database Manager
    SQLite database for storing all trading data
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path or DATABASE_PATH
        self.logger = get_logger(__name__)

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize connection
        self.conn = None
        self.cursor = None

        self._connect()
        self._create_tables()

        self.logger.info(f"Database initialized: {self.db_path}")

    def _connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.logger.debug("Database connected")
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise

    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            # Trades table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    pnl REAL,
                    status TEXT NOT NULL,
                    strategy TEXT,
                    tag TEXT,
                    exit_timestamp TEXT
                )
            ''')

            # Orders table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    order_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    order_type TEXT NOT NULL,
                    price REAL,
                    trigger_price REAL,
                    status TEXT NOT NULL,
                    tag TEXT
                )
            ''')

            # Daily summary table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    gross_profit REAL,
                    gross_loss REAL,
                    net_pnl REAL,
                    win_rate REAL,
                    avg_win REAL,
                    avg_loss REAL,
                    max_drawdown REAL
                )
            ''')

            self.conn.commit()
            self.logger.debug("Database tables created/verified")

        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise

    # =========================================================================
    # TRADE LOGGING
    # =========================================================================

    def log_trade_entry(self, symbol: str, transaction_type: str, quantity: int,
                       entry_price: float, strategy: str = None, tag: str = None) -> int:
        """
        Log trade entry

        Args:
            symbol: Trading symbol
            transaction_type: 'BUY' or 'SELL'
            quantity: Quantity
            entry_price: Entry price
            strategy: Strategy name
            tag: Optional tag

        Returns:
            Trade ID
        """
        try:
            self.cursor.execute('''
                INSERT INTO trades (timestamp, symbol, transaction_type, quantity, entry_price, status, strategy, tag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), symbol, transaction_type, quantity, entry_price, 'OPEN', strategy, tag))

            self.conn.commit()
            trade_id = self.cursor.lastrowid

            self.logger.info(f"Trade entry logged: ID={trade_id}, {symbol}")
            return trade_id

        except Exception as e:
            self.logger.error(f"Error logging trade entry: {e}")
            return -1

    def log_trade_exit(self, trade_id: int, exit_price: float, pnl: float):
        """
        Log trade exit

        Args:
            trade_id: Trade ID from entry
            exit_price: Exit price
            pnl: Profit/Loss
        """
        try:
            self.cursor.execute('''
                UPDATE trades
                SET exit_price = ?, pnl = ?, status = 'CLOSED', exit_timestamp = ?
                WHERE id = ?
            ''', (exit_price, pnl, datetime.now().isoformat(), trade_id))

            self.conn.commit()
            self.logger.info(f"Trade exit logged: ID={trade_id}, P&L=₹{pnl:.2f}")

        except Exception as e:
            self.logger.error(f"Error logging trade exit: {e}")

    def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        try:
            self.cursor.execute("SELECT * FROM trades WHERE status = 'OPEN'")
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Error getting open trades: {e}")
            return []

    def get_closed_trades(self, limit: int = 100) -> List[Dict]:
        """Get closed trades"""
        try:
            self.cursor.execute(f"SELECT * FROM trades WHERE status = 'CLOSED' ORDER BY exit_timestamp DESC LIMIT {limit}")
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Error getting closed trades: {e}")
            return []

    # =========================================================================
    # ORDER LOGGING
    # =========================================================================

    def log_order(self, order_id: str, symbol: str, transaction_type: str, quantity: int,
                 order_type: str, price: float = None, trigger_price: float = None,
                 status: str = 'PLACED', tag: str = None):
        """Log order details"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO orders (timestamp, order_id, symbol, transaction_type, quantity, order_type, price, trigger_price, status, tag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), order_id, symbol, transaction_type, quantity, order_type, price, trigger_price, status, tag))

            self.conn.commit()

        except Exception as e:
            self.logger.error(f"Error logging order: {e}")

    def update_order_status(self, order_id: str, status: str):
        """Update order status"""
        try:
            self.cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
            self.conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating order status: {e}")

    # =========================================================================
    # DAILY SUMMARY
    # =========================================================================

    def save_daily_summary(self, date: str, summary: Dict):
        """
        Save daily trading summary

        Args:
            date: Date string (YYYY-MM-DD)
            summary: Summary dictionary
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO daily_summary
                (date, total_trades, winning_trades, losing_trades, gross_profit, gross_loss, net_pnl, win_rate, avg_win, avg_loss, max_drawdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date,
                summary.get('total_trades', 0),
                summary.get('winning_trades', 0),
                summary.get('losing_trades', 0),
                summary.get('gross_profit', 0),
                summary.get('gross_loss', 0),
                summary.get('net_pnl', 0),
                summary.get('win_rate', 0),
                summary.get('avg_win', 0),
                summary.get('avg_loss', 0),
                summary.get('max_drawdown', 0)
            ))

            self.conn.commit()
            self.logger.info(f"Daily summary saved for {date}")

        except Exception as e:
            self.logger.error(f"Error saving daily summary: {e}")

    def get_daily_summary(self, date: str) -> Optional[Dict]:
        """Get daily summary for specific date"""
        try:
            self.cursor.execute("SELECT * FROM daily_summary WHERE date = ?", (date,))
            row = self.cursor.fetchone()

            if row:
                columns = [desc[0] for desc in self.cursor.description]
                return dict(zip(columns, row))

            return None

        except Exception as e:
            self.logger.error(f"Error getting daily summary: {e}")
            return None

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    def get_trades_dataframe(self, days: int = 30) -> pd.DataFrame:
        """Get trades as pandas DataFrame"""
        try:
            query = f"SELECT * FROM trades WHERE status = 'CLOSED' ORDER BY exit_timestamp DESC LIMIT {days * 10}"
            df = pd.read_sql_query(query, self.conn)
            return df

        except Exception as e:
            self.logger.error(f"Error getting trades dataframe: {e}")
            return pd.DataFrame()

    def calculate_performance_metrics(self) -> Dict:
        """Calculate overall performance metrics"""
        try:
            df = self.get_trades_dataframe(days=365)

            if df.empty:
                return {}

            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])

            gross_profit = df[df['pnl'] > 0]['pnl'].sum()
            gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
            net_pnl = df['pnl'].sum()

            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
            avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'net_pnl': net_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor
            }

        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")


# =============================================================================
# TESTING
# =============================================================================
if __name__ == "__main__":
    print("Testing Database Module...")
    print("="*60)

    db = TradingDatabase("data/test_trading.db")

    print("\n1. Logging Trade Entry")
    trade_id = db.log_trade_entry("NIFTY24NOV24000CE", "BUY", 50, 150.0, strategy="TestStrategy")
    print(f"   Trade ID: {trade_id}")

    print("\n2. Logging Trade Exit")
    db.log_trade_exit(trade_id, 160.0, 500.0)

    print("\n3. Getting Closed Trades")
    trades = db.get_closed_trades(limit=10)
    print(f"   Closed trades: {len(trades)}")

    print("\n4. Performance Metrics")
    metrics = db.calculate_performance_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")

    db.close()

    print("\n" + "="*60)
    print("✓ All tests completed!")
