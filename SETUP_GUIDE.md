# 🚀 Complete Setup Guide - Nifty Options Trading Platform

This guide will walk you through setting up the platform from scratch.

---

## 📋 Prerequisites

1. **Zerodha Trading Account**
   - Active Zerodha trading account
   - Funds available for trading

2. **Kite Connect App**
   - Register at: https://developers.kite.trade/
   - Create a new app
   - Get API Key and API Secret

3. **Python 3.9+**
   - Python installed on your system
   - pip package manager

---

## 🔧 Step-by-Step Setup

### **Step 1: Install Dependencies**

```bash
# Navigate to project directory
cd my-app

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### **Step 2: Configure Kite Connect App**

1. **Go to Kite Connect Developer Portal:**
   - Visit: https://developers.kite.trade/apps
   - Login with your Zerodha credentials

2. **Create New App (if you haven't already):**
   - Click "Create new app"
   - Fill in details:
     - **App name:** My Algo Trading Platform (or any name)
     - **App type:** Connect
     - **Redirect URL:** `http://127.0.0.1` ⚠️ **IMPORTANT**
     - **Description:** Automated Nifty Options Trading

3. **Copy Your Credentials:**
   - **API Key:** (looks like: abcdef123456)
   - **API Secret:** (looks like: xyz789abc123)

### **Step 3: Configure the Platform**

```bash
# Copy config template
cp config/config.ini.template config/config.ini

# Edit config.ini
nano config/config.ini  # or use any text editor
```

**Add your Kite credentials:**

```ini
[kite]
api_key = YOUR_API_KEY_HERE
api_secret = YOUR_API_SECRET_HERE
access_token =
user_id = YOUR_ZERODHA_CLIENT_ID

[safety]
paper_trading = true    # ⚠️ KEEP THIS TRUE FOR TESTING!
```

**Important:** Leave `access_token` empty for now - we'll generate it in next step.

### **Step 4: Generate Access Token**

The platform provides two helper scripts to make this easy:

#### **4a. Get Login URL**

```bash
python step1_get_login_url.py
```

This will output:
- A login URL for Zerodha
- Instructions on what to do next

#### **4b. Login to Zerodha**

1. **Copy the login URL** from step 4a
2. **Open it in your browser**
3. **Login** with your Zerodha credentials:
   - User ID
   - Password
   - 2FA code
4. **After login**, you'll be redirected to a URL like:
   ```
   http://127.0.0.1/?request_token=XXXXXXXXX&action=login&status=success
   ```
5. **Copy the `request_token`** value (the XXXXXXXXX part)

#### **4c. Generate Access Token**

```bash
python step2_generate_token.py
```

- Paste the `request_token` from step 4b
- Script will generate and save your access token automatically
- ✅ You're ready to run the platform!

---

## ✅ Verify Setup

Test that everything is configured correctly:

```bash
# Test configuration
python -c "from config.config import print_config, validate_config; print_config(); print(validate_config())"

# Test market data module
python src/data/market_data.py

# Test options chain
python src/data/options_chain.py
```

If all tests pass, you're ready to go! ✅

---

## 🎯 Run the Platform

### **First Time (Paper Trading)**

```bash
# Start the trading platform
python main.py
```

**What happens:**
- Platform starts in PAPER TRADING mode (safe, no real orders)
- Connects to Zerodha to fetch real market data
- Monitors Nifty options in real-time
- Simulates trades based on strategy signals
- Logs everything to `logs/` directory

**Monitor the logs:**

```bash
# In another terminal window
tail -f logs/trading_$(date +%Y%m%d).log
```

### **Daily Workflow**

Since access tokens expire daily:

```bash
# Every trading day morning:

# 1. Generate fresh access token
python step1_get_login_url.py
# (Open URL, login, copy request_token)

python step2_generate_token.py
# (Paste request_token)

# 2. Start trading platform
python main.py
```

---

## 📱 Optional: Setup Telegram Alerts

Get real-time notifications on your phone:

### **1. Create Telegram Bot**

1. Open Telegram app
2. Search for `@BotFather`
3. Send `/newbot` command
4. Follow instructions to create bot
5. **Copy the bot token** (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)

### **2. Get Your Chat ID**

1. **Start your bot** (search for it in Telegram and send `/start`)
2. **Get updates:**
   - Open browser and go to:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   - Replace `<YOUR_BOT_TOKEN>` with your actual bot token
3. **Copy the chat ID** from response (looks like: 123456789)

### **3. Update Config**

Add to `config/config.ini`:

```ini
[telegram]
enabled = true
bot_token = YOUR_BOT_TOKEN_HERE
chat_id = YOUR_CHAT_ID_HERE
alerts_enabled = true
```

Now you'll get notifications for:
- Trade entries/exits
- Risk alerts
- Daily summary
- System errors

---

## 🔍 Troubleshooting

### **Problem: "No access token found"**

**Solution:**
- Run `python step2_generate_token.py`
- Make sure token is saved to `config/config.ini`
- Or set environment variable: `export KITE_ACCESS_TOKEN=your_token`

### **Problem: "Invalid request_token" or "Token expired"**

**Reason:** Request tokens are single-use and expire in minutes.

**Solution:**
- Run `python step1_get_login_url.py` again
- Get a fresh request_token
- Use it immediately in step 2

### **Problem: "Redirect mismatch" error during login**

**Reason:** Redirect URL in Kite app doesn't match.

**Solution:**
- Go to https://developers.kite.trade/apps
- Edit your app
- Set Redirect URL to **exactly**: `http://127.0.0.1`
- Save changes
- Try authentication again

### **Problem: "Insufficient margin" error**

**Solution:**
- Check funds in your Zerodha account
- Reduce `max_lots_per_trade` in config
- Ensure you have intraday margin available

### **Problem: Platform exits immediately**

**Check:**
- Is market open? (9:15 AM - 3:30 PM on weekdays)
- Check logs in `logs/` directory for errors
- Verify access token is valid
- Run individual module tests to isolate issue

---

## 🎓 Understanding the Platform

### **Paper Trading vs Live Trading**

| Paper Trading (Safe) | Live Trading (Real Money) |
|---------------------|---------------------------|
| ✅ No real orders | ⚠️ Real orders placed |
| ✅ Zero financial risk | ⚠️ Real money at risk |
| ✅ Uses real market data | ✅ Uses real market data |
| ✅ All features work | ✅ All features work |
| ✅ Perfect for testing | ⚠️ Only when confident |

**ALWAYS start with `paper_trading = true` in config!**

### **Platform Components**

```
Trading Flow:
Market Data → Strategy → Risk Check → Order Execution → Position Tracking
                                ↓
                          Circuit Breakers
                                ↓
                          Database Logging
                                ↓
                         Telegram Alerts
```

### **Log Files**

All logs are in `logs/` directory:

- **`trading_YYYYMMDD.log`** - All platform activities
- **`errors_YYYYMMDD.log`** - Errors only
- **`trades_YYYYMMDD.log`** - All trades (entries/exits)

### **Database**

All trades stored in `data/trading.db` (SQLite):

```bash
# View trades
sqlite3 data/trading.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"

# View daily summary
sqlite3 data/trading.db "SELECT * FROM daily_summary;"
```

---

## 🚦 Before Going Live

**Complete this checklist before enabling live trading:**

- [ ] Tested in paper mode for at least 2 weeks
- [ ] Reviewed all logs and understand platform behavior
- [ ] Comfortable with strategy logic
- [ ] Set conservative risk limits (start with ₹5,000 daily loss)
- [ ] Start with only 1 lot per trade
- [ ] Have emergency stop plan ready
- [ ] Monitor continuously during market hours
- [ ] Telegram alerts configured and working
- [ ] Understand how to manually exit positions
- [ ] Know how to stop the platform quickly (Ctrl+C)

**To enable live trading:**

```ini
# config/config.ini
[safety]
paper_trading = false    # ⚠️ ONLY AFTER THOROUGH TESTING!
```

---

## 📞 Support

- **Issues:** Check logs in `logs/` directory
- **Documentation:** Read README.md and code comments
- **Zerodha API:** https://kite.trade/docs/connect/v3/
- **Trading Q&A:** https://tradingqna.com/

---

## ⚠️ Final Reminder

**THIS IS REAL MONEY TRADING:**
- Always start with paper trading
- Never risk more than you can afford to lose
- Monitor positions continuously
- Respect risk limits
- Stop trading if you're not comfortable
- Consult a financial advisor if unsure

---

**You're all set! Start with paper trading and happy trading! 🚀**
