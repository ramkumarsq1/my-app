# ⚡ Quick Start Guide - 5 Minutes to Running Platform

**Get up and running in 5 minutes!**

---

## 🚀 Quick Installation

```bash
# 1. Install dependencies (FIRST TIME ONLY)
python install_dependencies.py

# 2. Configure credentials
cp config/config.ini.template config/config.ini
nano config/config.ini  # Add your Kite API key and secret

# 3. Generate access token
python step1_get_login_url.py  # Get login URL
# Open URL in browser, login, copy request_token

python step2_generate_token.py  # Generate token
# Paste request_token

# 4. Run the platform
python main.py
```

---

## 📝 Before You Start

### **1. Get Kite Connect Credentials**

- Register at: https://developers.kite.trade/
- Create new app
- Set **Redirect URL** to: `http://127.0.0.1`
- Copy your **API Key** and **API Secret**

### **2. Have These Ready**

- ✅ Zerodha trading account
- ✅ Kite Connect API Key
- ✅ Kite Connect API Secret
- ✅ Python 3.9 or higher installed

---

## 🔧 Detailed Steps

### **Step 1: Install Dependencies**

```bash
# Option A: Using installer script (Recommended)
python install_dependencies.py

# Option B: Manual installation
pip install -r requirements.txt

# Option C: Using virtual environment (Best practice)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "import kiteconnect, pandas, numpy; print('✅ All dependencies OK')"
```

### **Step 2: Configure Platform**

```bash
# Copy configuration template
cp config/config.ini.template config/config.ini

# Edit configuration
nano config/config.ini  # or use any text editor
```

**Add your Kite credentials:**
```ini
[kite]
api_key = YOUR_API_KEY_HERE
api_secret = YOUR_API_SECRET_HERE
user_id = YOUR_ZERODHA_CLIENT_ID
```

**Important settings:**
```ini
[safety]
paper_trading = true    # Keep TRUE for testing!

[risk]
max_daily_loss = 15000   # Start conservative
max_lots_per_trade = 1   # Start with 1 lot
```

### **Step 3: Authenticate (Generate Access Token)**

Access tokens expire daily, so you'll do this every trading day:

```bash
# 3a. Get login URL
python step1_get_login_url.py
```

**Output:**
```
Open this URL in your browser:
https://kite.zerodha.com/connect/login?api_key=xxxxx&v=3
```

1. **Copy the URL** and open in browser
2. **Login** with Zerodha credentials
3. After login, you'll be redirected to:
   ```
   http://127.0.0.1/?request_token=ABC123XYZ&action=login&status=success
   ```
4. **Copy the request_token** (the ABC123XYZ part)

```bash
# 3b. Generate access token
python step2_generate_token.py
```

- Paste the request_token when prompted
- ✅ Access token will be saved automatically

### **Step 4: Run Platform**

```bash
python main.py
```

**You should see:**
```
================================================================================
NIFTY OPTIONS TRADING PLATFORM
================================================================================
PAPER TRADING MODE ENABLED - NO REAL ORDERS WILL BE PLACED
================================================================================

Market Status:
  Nifty Spot: 24,150.75
  ATM Strike: 24150
  Market Open: True
  Trading Allowed: True
  ...
```

---

## 📊 Monitor Platform

### **View Logs (Real-time)**

```bash
# Trading log
tail -f logs/trading_$(date +%Y%m%d).log

# Errors only
tail -f logs/errors_$(date +%Y%m%d).log

# Trades only
tail -f logs/trades_$(date +%Y%m%d).log
```

### **Check Database**

```bash
# View recent trades
sqlite3 data/trading.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"

# Daily summary
sqlite3 data/trading.db "SELECT * FROM daily_summary;"
```

---

## 🛑 Common Issues & Quick Fixes

### **Issue: ModuleNotFoundError: No module named 'dotenv'**

**Fix:**
```bash
pip install python-dotenv
# Or run:
python install_dependencies.py
```

### **Issue: No access token found**

**Fix:**
```bash
python step1_get_login_url.py
python step2_generate_token.py
```

### **Issue: Redirect mismatch error**

**Fix:**
- Go to https://developers.kite.trade/apps
- Edit your app
- Set Redirect URL to: `http://127.0.0.1` (exactly)

### **Issue: Platform exits immediately**

**Check:**
- Is market open? (9:15 AM - 3:30 PM IST, Mon-Fri)
- Check logs: `cat logs/errors_$(date +%Y%m%d).log`
- Verify access token: `grep access_token config/config.ini`

---

## ✅ Verify Everything is Working

Run these test commands:

```bash
# 1. Test configuration
python -c "from config.config import print_config; print_config()"

# 2. Test market data
python src/data/market_data.py

# 3. Test options chain
python src/data/options_chain.py

# 4. Test order manager (paper trading)
python src/execution/order_manager.py
```

All tests should pass ✅

---

## 📱 Optional: Setup Telegram Alerts

Get notifications on your phone:

1. **Create bot with @BotFather:**
   - Send `/newbot` to @BotFather on Telegram
   - Copy bot token

2. **Get chat ID:**
   - Start your bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Copy chat ID from response

3. **Update config:**
   ```ini
   [telegram]
   enabled = true
   bot_token = YOUR_BOT_TOKEN
   chat_id = YOUR_CHAT_ID
   ```

---

## 🎯 Daily Routine

Since access tokens expire daily:

```bash
# Every trading morning (takes 2 minutes):

# 1. Generate token
python step1_get_login_url.py
# (Open URL, login, copy token)

python step2_generate_token.py
# (Paste token)

# 2. Start platform
python main.py

# 3. Monitor logs
tail -f logs/trading_$(date +%Y%m%d).log
```

---

## 📖 Next Steps

- ✅ Read full documentation: `README.md`
- ✅ Complete setup guide: `SETUP_GUIDE.md`
- ✅ Test in paper trading for 1-2 weeks
- ✅ Review logs daily
- ✅ Understand strategy logic
- ✅ Only then consider live trading

---

## ⚠️ Important Reminders

- 🛡️ **Always start with `paper_trading = true`**
- 🛡️ **Test for 2+ weeks before going live**
- 🛡️ **Start with 1 lot when going live**
- 🛡️ **Never override risk limits**
- 🛡️ **Monitor positions continuously**

---

**You're ready to go! Start the platform and watch it work with real market data in paper trading mode! 🚀**

**Having issues?** Check `SETUP_GUIDE.md` for detailed troubleshooting.
