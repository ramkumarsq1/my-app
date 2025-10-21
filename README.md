# Nifty Options Trading Platform

🤖 **Automated Trading System for NSE Nifty Weekly Options**

A robust, production-ready algorithmic trading platform for Nifty weekly options using Zerodha Kite Connect API. Built with safety, reliability, and capital preservation as top priorities.

---

## ⚠️ IMPORTANT SAFETY NOTICE

**THIS IS REAL MONEY TRADING SOFTWARE**

- **ALWAYS start with `PAPER_TRADING = True`** in config
- Test thoroughly before going live
- Understand all risks before trading
- Never risk more than you can afford to lose
- This software comes with NO WARRANTY
- Author is NOT responsible for any trading losses

---

## 🎯 Features

### Core Trading Capabilities
- ✅ **Dynamic Market Data** - Real-time Nifty spot price, options chain
- ✅ **Automated Weekly Expiry Detection** - Auto-detects current Thursday expiry
- ✅ **Dynamic Strike Selection** - ATM/OTM/ITM calculation based on live prices
- ✅ **Order Execution** - Market, Limit, Stop-Loss orders with retry logic
- ✅ **Position Tracking** - Real-time P&L, multi-leg positions
- ✅ **Paper Trading Mode** - Risk-free testing environment

### Risk Management (CRITICAL)
- 🛡️ **Daily Loss Limits** - Auto-stop trading at configured loss
- 🛡️ **Position Size Limits** - Max lots per trade, max open positions
- 🛡️ **Stop-Loss Enforcement** - Automatic SL for every trade
- 🛡️ **Circuit Breakers** - Halt trading on consecutive losses
- 🛡️ **Margin Monitoring** - Pre-trade margin availability checks
- 🛡️ **Force Exit** - Auto-squareoff before market close

### Strategy Framework
- 📊 **Modular Strategy System** - Easy to create custom strategies
- 📊 **Sample Strategy Included** - ATM Straddle strategy
- 📊 **Backtesting Support** - Test strategies on historical data
- 📊 **Multiple Strategy Support** - Run multiple strategies simultaneously

### Monitoring & Alerts
- 📱 **Telegram Notifications** - Real-time trade and risk alerts
- 📱 **Comprehensive Logging** - Trade logs, error logs, system logs
- 📱 **Database Storage** - All trades and orders stored in SQLite
- 📱 **Performance Metrics** - Win rate, profit factor, Sharpe ratio

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd my-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy config template
cp config/config.ini.template config/config.ini

# Edit config.ini and add your credentials
nano config/config.ini
```

**Required Configuration:**
- `KITE_API_KEY` - Your Zerodha API key
- `KITE_API_SECRET` - Your Zerodha API secret
- `KITE_ACCESS_TOKEN` - Generate using Kite login flow

**Important Settings:**
- `PAPER_TRADING = true` - ALWAYS start with paper trading
- `MAX_DAILY_LOSS = 15000` - Maximum daily loss in INR
- `MAX_LOTS_PER_TRADE = 2` - Maximum lot size per trade

### 3. Generate Access Token

```python
# Run this to get login URL
python -c "
from src.api.kite_wrapper import KiteWrapper
from config.config import KITE_API_KEY
kite = KiteWrapper(api_key=KITE_API_KEY)
print(kite.kite.login_url())
"

# 1. Open the URL in browser
# 2. Login to Zerodha
# 3. Copy 'request_token' from redirect URL
# 4. Generate access token:

python -c "
from src.api.kite_wrapper import KiteWrapper
from config.config import KITE_API_KEY, KITE_API_SECRET
kite = KiteWrapper(api_key=KITE_API_KEY)
token = kite.generate_session('YOUR_REQUEST_TOKEN')
print(f'Access Token: {token}')
"

# 5. Copy access token to config.ini
```

### 4. Test the System

```bash
# Test configuration
python -c "
from config.config import print_config, validate_config
print_config()
print(validate_config())
"

# Test market data (paper trading mode)
python src/data/market_data.py

# Test options chain
python src/data/options_chain.py
```

### 5. Run the Platform

```bash
# Start in paper trading mode (SAFE)
python main.py

# Monitor logs
tail -f logs/trading_$(date +%Y%m%d).log
```

---

## 📁 Project Structure

```
my-app/
├── config/
│   ├── config.py              # Configuration management
│   └── config.ini.template    # Configuration template
│
├── src/
│   ├── api/
│   │   └── kite_wrapper.py    # Zerodha Kite API wrapper
│   │
│   ├── data/
│   │   ├── market_data.py     # Market data & ATM calculations
│   │   └── options_chain.py   # Options chain & expiry management
│   │
│   ├── execution/
│   │   ├── order_manager.py   # Order placement & tracking
│   │   └── position_manager.py # Position & P&L tracking
│   │
│   ├── risk/
│   │   └── risk_manager.py    # Risk management & circuit breakers
│   │
│   ├── strategies/
│   │   ├── base_strategy.py   # Base strategy class
│   │   └── sample_strategy.py # Sample ATM Straddle strategy
│   │
│   ├── database/
│   │   └── database.py        # SQLite database for trades
│   │
│   ├── notifications/
│   │   └── telegram_bot.py    # Telegram notifications
│   │
│   └── utils/
│       └── logger.py          # Logging utility
│
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🎓 How It Works

### Trading Flow

1. **Market Data Collection** (Dynamic)
   - Fetch Nifty spot price in real-time
   - Calculate ATM strike automatically
   - Get options chain data for relevant strikes

2. **Strategy Signal Generation**
   - Strategy analyzes market conditions
   - Generates entry/exit signals
   - Calculates position size

3. **Risk Checks** (Before Every Trade)
   - Check daily loss limit
   - Verify margin availability
   - Validate position size
   - Check consecutive losses

4. **Order Execution**
   - Place orders via Kite API
   - Track order status
   - Handle partial fills
   - Retry on failures

5. **Position Management**
   - Track all open positions
   - Calculate real-time P&L
   - Monitor for exit signals
   - Auto-squareoff before market close

6. **Risk Monitoring**
   - Continuous risk level assessment
   - Trigger circuit breakers if needed
   - Send alerts for critical events
   - Log all activities

### Key Concepts

**Dynamic vs Static:**
- ✅ **Dynamic (Good):** ATM strike calculated from current spot price
- ❌ **Static (Bad):** Hardcoded strike like 24000

**Everything in this platform is DYNAMIC:**
- Spot price: Fetched from live market
- ATM strike: Calculated from spot price
- Expiry: Auto-detected (current Thursday)
- Position sizing: Based on available margin
- Risk limits: Enforced in real-time

---

## ⚙️ Configuration Guide

### Risk Management Settings

```ini
[risk]
max_loss_per_trade = 5000      # Max loss per single trade (INR)
max_daily_loss = 15000         # Max total daily loss (INR)
max_consecutive_losses = 3     # Halt trading after N losses
stop_loss_percentage = 40      # SL at 40% of entry price
target_percentage = 60         # Target at 60% profit
max_margin_utilization = 50    # Use max 50% of available margin
cooloff_period_minutes = 30    # Wait 30min after consecutive losses
```

### Trading Hours

```ini
[trading_hours]
market_open = 09:15     # NSE opening time
trading_start = 09:20   # Start trading (avoid first 5 min)
trading_end = 15:20     # Stop new trades
force_exit = 15:25      # Force exit all positions
```

### Safety Switches

```ini
[safety]
paper_trading = true           # ALWAYS start with true
trade_on_expiry = false        # Avoid expiry day trading
auto_square_off = true         # Auto-exit before market close
```

---

## 📊 Creating Custom Strategies

### Step 1: Create Strategy File

```python
# src/strategies/my_strategy.py

from src.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("MyStrategy")

    def generate_signal(self, market_data):
        # Your entry logic here
        if some_condition:
            return {
                'action': 'ENTRY',
                'symbol': symbol,
                'quantity': 1,
                'price': price
            }
        return None

    def should_exit(self, position, current_price):
        # Your exit logic here
        if exit_condition:
            return True, "Reason for exit"
        return False, "No exit"
```

### Step 2: Add to Trading Engine

```python
# In main.py
from src.strategies.my_strategy import MyStrategy

# In TradingEngine.__init__()
self.strategy = MyStrategy()
```

---

## 📱 Telegram Setup

1. **Create Bot:**
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Copy bot token

2. **Get Chat ID:**
   - Start your bot
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Copy `chat.id` from response

3. **Configure:**
   ```ini
   [telegram]
   enabled = true
   bot_token = YOUR_BOT_TOKEN
   chat_id = YOUR_CHAT_ID
   ```

---

## 🐛 Troubleshooting

### "No access token" error
- Generate fresh access token (expires daily with some brokers)
- Check config.ini has correct token
- Verify API key/secret are correct

### "Insufficient margin" error
- Check available margin in Zerodha account
- Reduce `max_lots_per_trade` in config
- Ensure you have funds for intraday trading

### Orders not executing
- Check if market is open
- Verify you're within trading hours (9:20-15:20)
- Check if paper_trading is enabled
- Review logs for detailed errors

### "Symbol not found" error
- Verify option symbol format: NIFTY24NOV24000CE
- Check if weekly expiry date is correct
- Ensure strike price exists in options chain

---

## 🔒 Security Best Practices

1. **Never Commit Credentials**
   - config.ini is in .gitignore
   - Never share API keys publicly
   - Rotate access tokens regularly

2. **Start Small**
   - Begin with 1 lot in paper trading
   - Test for at least 1-2 weeks
   - Gradually increase size

3. **Monitor Continuously**
   - Check positions every 30 minutes
   - Review logs daily
   - Set up Telegram alerts

4. **Respect Risk Limits**
   - Never override circuit breakers
   - Don't increase limits after losses
   - Take breaks after bad days

---

## 📈 Performance Monitoring

### Check Logs

```bash
# Today's trading log
tail -f logs/trading_$(date +%Y%m%d).log

# Error log
tail -f logs/errors_$(date +%Y%m%d).log

# Trade log
tail -f logs/trades_$(date +%Y%m%d).log
```

### Query Database

```python
from src.database.database import TradingDatabase

db = TradingDatabase()

# Get performance metrics
metrics = db.calculate_performance_metrics()
print(metrics)

# Get closed trades
trades = db.get_closed_trades(limit=100)
print(trades)
```

---

## ⚖️ Disclaimer

**IMPORTANT LEGAL NOTICE:**

1. This software is provided "AS IS" without any warranty
2. Trading involves substantial risk of loss
3. Past performance does not guarantee future results
4. Author is NOT responsible for any financial losses
5. Use at your own risk
6. Consult a financial advisor before trading
7. Ensure you understand options trading fully
8. Test thoroughly in paper trading mode first

**By using this software, you acknowledge:**
- You understand the risks of algorithmic trading
- You take full responsibility for all trading decisions
- You will not hold the author liable for any losses
- You will comply with all applicable laws and regulations
- You have read and understood this entire README

---

## 📞 Support & Community

- **Issues:** Report bugs via GitHub Issues
- **Questions:** Check existing issues before creating new ones
- **Contributions:** PRs welcome (follow coding standards)
- **Documentation:** Read all comments in code

---

## 📝 License

This project is for educational purposes. Use at your own risk.

---

## 🎯 Roadmap

**Phase 1: Foundation** ✅
- [x] Core trading infrastructure
- [x] Risk management system
- [x] Order execution
- [x] Position tracking

**Phase 2: Enhancement** 🚧
- [ ] Advanced backtesting engine
- [ ] More strategy templates
- [ ] Web dashboard
- [ ] Live performance charts

**Phase 3: Advanced Features** 📅
- [ ] Machine learning integration
- [ ] Multi-timeframe analysis
- [ ] Greeks-based strategies
- [ ] Portfolio optimization

---

## 🙏 Acknowledgments

- **Zerodha** - For the excellent Kite Connect API
- **NSE** - For options market data
- **Python Community** - For amazing open-source libraries

---

**Happy Trading! 🚀**

*Remember: The goal is consistent profitability, not home runs.*
*Protect your capital above all else.*
