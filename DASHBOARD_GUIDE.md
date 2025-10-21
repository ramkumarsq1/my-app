# 📊 Web Dashboard Guide

**Real-time web interface for monitoring your Nifty Options Trading Platform**

---

## 🚀 Quick Start

### **Launch Dashboard (One Command)**

```bash
python run_dashboard.py
```

That's it! The dashboard will open automatically in your browser at:
**http://localhost:8501**

---

## 🔐 Login

### **Default Credentials**

- **Username:** `admin`
- **Password:** `admin123`

⚠️ **IMPORTANT:** Change these credentials immediately after first login!

### **Change Password**

1. Login with default credentials
2. Click "🔐 Change Password" in sidebar
3. Enter current password
4. Set new username (optional) and password
5. Confirm new password
6. Click "Reset Password"

---

## 📊 Dashboard Features

### **1. Overview Tab** 📈

**Market Overview:**
- 🟢 Nifty 50 spot price (real-time)
- 📊 ATM strike calculation
- ⏰ Market status (Open/Closed)
- ⏳ Time remaining to market close
- 📉 OHLC data (Open, High, Low, Close)

**Recent Trades:**
- Last 20 trades executed
- Entry/Exit prices
- P&L for each trade
- Trade status

### **2. Options Chain Tab** 🔗

**Live Options Data:**
- Call (CE) and Put (PE) premiums
- Strike prices around ATM
- Volume and Open Interest
- ATM strike highlighted
- Refreshable data

### **3. Performance Tab** 📈

**Trading Statistics:**
- Total trades executed
- Win rate percentage
- Net P&L (Profit & Loss)
- Profit factor
- Average win/loss amounts
- Gross profit/loss breakdown

**Performance Charts:**
- Coming soon: P&L charts, win/loss distribution

### **4. Risk Monitor Tab** 🛡️

**Risk Limits:**
- Maximum daily loss limit
- Maximum lots per trade
- Trading window (start/end times)
- Current risk status

**Safety Information:**
- All limits enforced automatically
- Circuit breaker status
- Paper trading indicator

---

## ⚙️ Dashboard Controls

### **Sidebar Controls:**

| Button | Function |
|--------|----------|
| 🚪 Logout | Logout from dashboard |
| 🔄 Refresh Data | Manually refresh all data |
| 📜 View Logs | Info about log files location |
| 💾 Export Data | Info about database location |
| 🔐 Change Password | Change login credentials |

### **Auto-Refresh:**

Dashboard automatically refreshes data every 30 seconds when market is open.

---

## 🎯 How to Use

### **Daily Workflow**

```bash
# Morning (Before Market Opens)

# 1. Generate access token
python step1_get_login_url.py
python step2_generate_token.py

# 2. Launch dashboard
python run_dashboard.py

# 3. Login with credentials

# 4. Monitor dashboard during trading hours
```

### **Monitoring Trades**

1. **Check Overview Tab** - See current market status and recent trades
2. **Review Performance Tab** - Track your P&L and statistics
3. **Monitor Risk Tab** - Ensure you're within safety limits
4. **Check Options Chain** - View live premiums for planning

### **During Trading Hours**

- Dashboard updates automatically
- Click "🔄 Refresh" for immediate update
- Monitor P&L in real-time
- Check recent trades in Overview tab
- Watch for risk alerts

---

## 🖥️ Dashboard + Trading Engine

You can run both simultaneously:

### **Terminal 1: Trading Engine**
```bash
python main.py
```

### **Terminal 2: Dashboard**
```bash
python run_dashboard.py
```

### **Terminal 3: Logs (Optional)**
```bash
tail -f logs/trading_$(date +%Y%m%d).log
```

**Result:** Trading engine executes trades, dashboard shows real-time status!

---

## 📱 Access from Mobile/Tablet

### **On Same Network:**

1. Find your computer's IP address:
   ```bash
   # Linux/Mac
   ifconfig | grep "inet "

   # Windows
   ipconfig
   ```

2. On mobile browser, go to:
   ```
   http://YOUR_COMPUTER_IP:8501
   ```

   Example: `http://192.168.1.100:8501`

### **Security Note:**

⚠️ Dashboard is not secure for public internet access. Only use on trusted local network!

---

## 🛠️ Troubleshooting

### **Dashboard won't start**

**Issue:** Error launching dashboard

**Solutions:**
```bash
# Install dashboard dependencies
pip install streamlit plotly

# Or use automated installer
python run_dashboard.py
# (Will auto-install dependencies)
```

### **"No access token found" error**

**Issue:** Can't connect to Zerodha

**Solution:**
```bash
# Generate fresh access token
python step1_get_login_url.py
python step2_generate_token.py

# Restart dashboard
python run_dashboard.py
```

### **Data not updating**

**Issue:** Dashboard shows stale data

**Solutions:**
- Click "🔄 Refresh Data" button
- Check if market is open (9:15 AM - 3:30 PM IST)
- Verify access token is valid
- Check internet connection

### **Login page shows but can't login**

**Issue:** Forgotten password

**Solution:**
```bash
# Delete credentials file to reset to defaults
rm dashboard/credentials.json

# Restart dashboard
python run_dashboard.py

# Use default credentials: admin / admin123
```

### **Dashboard is slow**

**Issue:** Dashboard takes time to load

**Causes:**
- First load initializes all components
- Fetching live market data
- Large database of trades

**Solutions:**
- Wait for initialization (shown on first load)
- Reduce number of displayed trades
- Clear old database entries

---

## ⚡ Performance Tips

### **Faster Loading:**

1. **Keep browser tab open** - Reusing same tab is faster
2. **Don't refresh too frequently** - Auto-refresh is optimized
3. **Close unused tabs** - Reduces memory usage

### **Resource Usage:**

- **CPU:** Low (~2-5%)
- **RAM:** ~200-300 MB
- **Network:** Minimal (only API calls)

---

## 🔒 Security

### **Best Practices:**

✅ **DO:**
- Change default password immediately
- Use strong password (8+ characters)
- Only access on trusted networks
- Logout when done
- Keep credentials.json secure

❌ **DON'T:**
- Share dashboard login credentials
- Access over public WiFi
- Expose to internet (port 8501)
- Use default credentials in production

### **Credentials Storage:**

Credentials are stored in: `dashboard/credentials.json`
- Passwords are hashed (SHA256)
- File is gitignored (won't be committed)
- Delete file to reset to defaults

---

## 📊 Dashboard Architecture

```
┌─────────────────────────────────────┐
│     Web Browser (localhost:8501)    │
│  - Login Page                       │
│  - Dashboard Tabs                   │
│  - Real-time Updates                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    Streamlit Dashboard (app.py)     │
│  - Authentication (auth.py)         │
│  - Market Data Display              │
│  - Performance Metrics              │
│  - Options Chain Viewer             │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│   Kite API  │  │  Database   │
│  (Live Data)│  │  (Trades)   │
└─────────────┘  └─────────────┘
```

---

## 🎨 Customization

### **Change Port:**

Edit `run_dashboard.py`:
```python
"--server.port", "8501",  # Change to your preferred port
```

### **Change Theme:**

Create `.streamlit/config.toml` in project root:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

---

## 📚 Additional Resources

- **Streamlit Docs:** https://docs.streamlit.io/
- **Plotly Charts:** https://plotly.com/python/
- **Platform README:** README.md
- **Setup Guide:** SETUP_GUIDE.md

---

## 🆘 Support

**Having issues?**

1. Check this guide's troubleshooting section
2. Review logs: `logs/trading_*.log`
3. Check console output where dashboard is running
4. Verify all dependencies are installed

---

## 🎯 Coming Soon

**Future Features:**

- [ ] Live P&L charts
- [ ] Trade execution from dashboard
- [ ] Strategy parameter controls
- [ ] Email/Telegram alerts configuration
- [ ] Multi-user support
- [ ] Advanced analytics dashboard
- [ ] Export reports (PDF/Excel)

---

## ⚠️ Important Notes

1. **Dashboard is READ-ONLY** - It displays data but doesn't execute trades
2. **Trading engine runs separately** - Use `main.py` to execute trades
3. **Paper trading mode** - Dashboard shows "PAPER TRADING" when enabled
4. **Market hours only** - Some data only available during market hours
5. **Internet required** - Dashboard needs connection to fetch live data

---

**Enjoy your real-time trading dashboard! 📊🚀**

Need help? Check `SETUP_GUIDE.md` or `README.md` for more information.
