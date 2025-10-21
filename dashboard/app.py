"""
Nifty Options Trading Platform - Web Dashboard
Real-time monitoring and control interface using Streamlit
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import authentication
from auth import require_authentication, logout

from config.config import (
    PAPER_TRADING, MAX_DAILY_LOSS, MAX_LOTS_PER_TRADE,
    TRADING_START_TIME, TRADING_END_TIME, KITE_ACCESS_TOKEN
)
from src.utils.logger import get_logger
from src.api.kite_wrapper import KiteWrapper
from src.data.market_data import MarketData
from src.data.options_chain import OptionsChain
from src.database.database import TradingDatabase

# Page configuration
st.set_page_config(
    page_title="Nifty Options Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, #f0f2f6 0%, #e6e9ef 100%);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .profit {
        color: #28a745;
        font-weight: bold;
    }
    .loss {
        color: #dc3545;
        font-weight: bold;
    }
    .warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize logger
logger = get_logger("Dashboard")

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.kite = None
    st.session_state.market_data = None
    st.session_state.options_chain = None
    st.session_state.database = None
    st.session_state.last_update = None

def initialize_components():
    """Initialize trading components"""
    try:
        if not KITE_ACCESS_TOKEN:
            st.error("❌ No access token found. Please run authentication scripts first.")
            st.stop()

        with st.spinner("Initializing components..."):
            st.session_state.kite = KiteWrapper()
            st.session_state.market_data = MarketData(st.session_state.kite)
            st.session_state.options_chain = OptionsChain(
                st.session_state.kite,
                st.session_state.market_data
            )
            st.session_state.database = TradingDatabase()
            st.session_state.initialized = True
            st.session_state.last_update = datetime.now()

        st.success("✅ Components initialized successfully!")
        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Initialization failed: {e}")
        st.stop()

def get_market_status():
    """Get current market status"""
    try:
        return st.session_state.market_data.get_market_status_summary()
    except Exception as e:
        st.error(f"Error fetching market status: {e}")
        return {}

def get_trading_stats():
    """Get trading statistics from database"""
    try:
        return st.session_state.database.calculate_performance_metrics()
    except Exception as e:
        st.error(f"Error fetching trading stats: {e}")
        return {}

def get_recent_trades(limit=10):
    """Get recent trades from database"""
    try:
        return st.session_state.database.get_closed_trades(limit=limit)
    except Exception as e:
        st.error(f"Error fetching recent trades: {e}")
        return []

def display_header():
    """Display dashboard header"""
    st.markdown('<div class="main-header">📈 Nifty Options Trading Dashboard</div>', unsafe_allow_html=True)

    # Trading mode indicator
    if PAPER_TRADING:
        st.warning("⚠️ **PAPER TRADING MODE** - No real orders will be placed")
    else:
        st.error("🔴 **LIVE TRADING MODE** - Real money at risk!")

def display_market_overview():
    """Display market overview section"""
    st.subheader("🌐 Market Overview")

    status = get_market_status()

    if not status:
        st.warning("Unable to fetch market data")
        return

    # Market metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        nifty_spot = status.get('nifty_spot', 0)
        change_pct = status.get('change_percent', 0)

        st.metric(
            label="Nifty 50",
            value=f"₹{nifty_spot:,.2f}",
            delta=f"{change_pct:+.2f}%"
        )

    with col2:
        atm_strike = status.get('atm_strike', 0)
        st.metric(
            label="ATM Strike",
            value=f"{atm_strike}"
        )

    with col3:
        market_open = status.get('market_open', False)
        st.metric(
            label="Market Status",
            value="🟢 OPEN" if market_open else "🔴 CLOSED"
        )

    with col4:
        minutes_left = status.get('minutes_to_close', 0)
        st.metric(
            label="Time to Close",
            value=f"{minutes_left} min"
        )

    # OHLC data
    with st.expander("📊 OHLC Data"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Open", f"₹{status.get('open', 0):,.2f}")
        with col2:
            st.metric("High", f"₹{status.get('high', 0):,.2f}")
        with col3:
            st.metric("Low", f"₹{status.get('low', 0):,.2f}")

def display_options_chain():
    """Display options chain data"""
    st.subheader("🔗 Options Chain")

    try:
        with st.spinner("Fetching options chain..."):
            chain_df = st.session_state.options_chain.get_option_chain_data(num_strikes=5)

        if chain_df.empty:
            st.warning("No options chain data available")
            return

        # Pivot table for better display
        ce_df = chain_df[chain_df['type'] == 'CE'][['strike', 'ltp', 'volume', 'oi']].copy()
        pe_df = chain_df[chain_df['type'] == 'PE'][['strike', 'ltp', 'volume', 'oi']].copy()

        ce_df.columns = ['Strike', 'CE LTP', 'CE Volume', 'CE OI']
        pe_df.columns = ['Strike', 'PE LTP', 'PE Volume', 'PE OI']

        # Merge on strike
        display_df = pd.merge(ce_df, pe_df, on='Strike', how='outer').sort_values('Strike')

        # Highlight ATM
        atm_strike = st.session_state.market_data.calculate_atm_strike()

        st.dataframe(
            display_df.style.apply(
                lambda x: ['background-color: #ffffcc' if x.name == atm_strike else '' for i in x],
                axis=1
            ),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error displaying options chain: {e}")

def display_trading_stats():
    """Display trading statistics"""
    st.subheader("📊 Trading Performance")

    stats = get_trading_stats()

    if not stats:
        st.info("No trading statistics available yet. Start trading to see stats!")
        return

    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_trades = stats.get('total_trades', 0)
        st.metric("Total Trades", total_trades)

    with col2:
        win_rate = stats.get('win_rate', 0)
        st.metric("Win Rate", f"{win_rate:.1f}%")

    with col3:
        net_pnl = stats.get('net_pnl', 0)
        pnl_class = "profit" if net_pnl > 0 else "loss"
        st.metric(
            "Net P&L",
            f"₹{net_pnl:,.2f}",
            delta=f"{'Profit' if net_pnl > 0 else 'Loss'}"
        )

    with col4:
        profit_factor = stats.get('profit_factor', 0)
        st.metric("Profit Factor", f"{profit_factor:.2f}")

    # Detailed stats
    with st.expander("📈 Detailed Statistics"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Trade Breakdown:**")
            st.write(f"- Winning Trades: {stats.get('winning_trades', 0)}")
            st.write(f"- Losing Trades: {stats.get('losing_trades', 0)}")
            st.write(f"- Average Win: ₹{stats.get('avg_win', 0):,.2f}")
            st.write(f"- Average Loss: ₹{stats.get('avg_loss', 0):,.2f}")

        with col2:
            st.write("**P&L Summary:**")
            st.write(f"- Gross Profit: ₹{stats.get('gross_profit', 0):,.2f}")
            st.write(f"- Gross Loss: ₹{stats.get('gross_loss', 0):,.2f}")
            st.write(f"- Net P&L: ₹{stats.get('net_pnl', 0):,.2f}")

def display_recent_trades():
    """Display recent trades"""
    st.subheader("📝 Recent Trades")

    trades = get_recent_trades(limit=20)

    if not trades:
        st.info("No trades yet. Trades will appear here once executed.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(trades)

    # Select relevant columns
    display_columns = ['timestamp', 'symbol', 'transaction_type', 'quantity',
                      'entry_price', 'exit_price', 'pnl', 'status']

    if all(col in df.columns for col in display_columns):
        df_display = df[display_columns].copy()

        # Format columns
        df_display['pnl'] = df_display['pnl'].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else "N/A")
        df_display['entry_price'] = df_display['entry_price'].apply(lambda x: f"₹{x:.2f}")
        df_display['exit_price'] = df_display['exit_price'].apply(lambda x: f"₹{x:.2f}" if pd.notna(x) else "N/A")

        st.dataframe(df_display, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

def display_risk_monitor():
    """Display risk monitoring panel"""
    st.subheader("🛡️ Risk Monitor")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Max Daily Loss",
            f"₹{MAX_DAILY_LOSS:,}"
        )

    with col2:
        st.metric(
            "Max Lots/Trade",
            MAX_LOTS_PER_TRADE
        )

    with col3:
        st.metric(
            "Trading Window",
            f"{TRADING_START_TIME} - {TRADING_END_TIME}"
        )

    # Risk alerts
    st.info("💡 All risk limits are enforced automatically by the risk manager")

def display_sidebar():
    """Display sidebar with controls"""
    with st.sidebar:
        # User info and logout
        if 'username' in st.session_state and st.session_state.username:
            st.write(f"👤 **User:** {st.session_state.username}")

        if st.button("🚪 Logout", use_container_width=True):
            logout()

        st.divider()

        st.header("⚙️ Controls")

        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state.last_update = datetime.now()
            st.rerun()

        # Last update time
        if st.session_state.last_update:
            st.caption(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")

        st.divider()

        # System info
        st.header("ℹ️ System Info")
        st.write(f"**Mode:** {'Paper Trading' if PAPER_TRADING else 'Live Trading'}")
        st.write(f"**Access Token:** {'✅ Connected' if KITE_ACCESS_TOKEN else '❌ Missing'}")

        st.divider()

        # Quick actions
        st.header("🚀 Quick Actions")

        if st.button("📜 View Logs", use_container_width=True):
            st.info("Check logs/ directory for detailed logs")

        if st.button("💾 Export Data", use_container_width=True):
            st.info("Database: data/trading.db")

        if st.button("🔐 Change Password", use_container_width=True):
            st.session_state.show_reset = True
            st.rerun()

        st.divider()

        # Documentation links
        st.header("📚 Documentation")
        st.markdown("- [Quick Start](../QUICK_START.md)")
        st.markdown("- [Setup Guide](../SETUP_GUIDE.md)")
        st.markdown("- [README](../README.md)")

def main():
    """Main dashboard function"""

    # Require authentication
    require_authentication()

    # Initialize components if not done
    if not st.session_state.initialized:
        display_header()
        st.info("👋 Welcome! Initializing trading platform...")

        if st.button("Initialize Platform", type="primary"):
            initialize_components()

        st.stop()

    # Display header
    display_header()

    # Display sidebar
    display_sidebar()

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔗 Options Chain", "📈 Performance", "🛡️ Risk"])

    with tab1:
        display_market_overview()
        st.divider()
        display_recent_trades()

    with tab2:
        display_options_chain()

    with tab3:
        display_trading_stats()

    with tab4:
        display_risk_monitor()

    # Auto-refresh every 30 seconds
    time.sleep(0.1)  # Small delay to prevent too frequent reruns

if __name__ == "__main__":
    main()
