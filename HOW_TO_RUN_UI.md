# 🚀 How to Run the User Interface

**Quick guide to launch and use the web dashboard**

---

## ⚡ Super Quick Start (3 Steps)

```bash
# Step 1: Install dependencies (first time only)
python install_dependencies.py

# Step 2: Generate access token (daily)
python step1_get_login_url.py
python step2_generate_token.py

# Step 3: Launch dashboard
python run_dashboard.py
```

**Dashboard opens automatically at:** `http://localhost:8501`

---

## 🔐 Login

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **Change these immediately after first login!**

---

## 📊 What You'll See

### **Dashboard Tabs:**

1. **📊 Overview** - Market data, recent trades
2. **🔗 Options Chain** - Live CE/PE premiums
3. **📈 Performance** - P&L, statistics, win rate
4. **🛡️ Risk** - Safety limits and controls

### **Live Data Displayed:**

✅ Nifty 50 spot price (real-time)
✅ ATM strike (dynamic calculation)
✅ Market status (Open/Closed)
✅ Time to market close
✅ Options chain with volumes
✅ Recent trades with P&L
✅ Trading statistics
✅ Risk limits status

---

## 🎮 How to Use

### **Monitor Trading:**

1. **Launch dashboard** while trading engine is running
2. **Overview tab** shows current market + recent trades
3. **Performance tab** shows your P&L and stats
4. **Options Chain** shows live premiums
5. **Auto-refreshes** every 30 seconds

### **Manual Refresh:**

Click "🔄 Refresh Data" button in sidebar anytime

### **Change Password:**

1. Click "🔐 Change Password" in sidebar
2. Enter current password
3. Set new credentials
4. Click "Reset Password"

### **Logout:**

Click "🚪 Logout" button in sidebar

---

## 🎯 Running Both Together

**Best Setup:** Run dashboard + trading engine simultaneously

### **Terminal 1: Trading Engine**
```bash
python main.py
```
Executes trades based on strategy

### **Terminal 2: Dashboard**
```bash
python run_dashboard.py
```
Shows real-time status

### **Result:**
- Engine trades automatically
- Dashboard shows live updates
- You monitor everything in browser

---

## 📱 Access from Phone/Tablet

**On same WiFi network:**

1. Find your computer's IP:
   ```bash
   # Linux/Mac
   hostname -I

   # Windows
   ipconfig
   ```

2. On mobile browser:
   ```
   http://YOUR_IP_ADDRESS:8501
   ```
   Example: `http://192.168.1.100:8501`

---

## 🛠️ Troubleshooting

### **Dashboard won't start**

```bash
# Install streamlit and plotly
pip install streamlit plotly

# Or run installer
python run_dashboard.py
# (Auto-installs dependencies)
```

### **"No access token" error**

```bash
# Generate new token
python step1_get_login_url.py
python step2_generate_token.py

# Restart dashboard
python run_dashboard.py
```

### **Forgot password**

```bash
# Delete credentials file
rm dashboard/credentials.json

# Restart dashboard
python run_dashboard.py

# Login with default: admin / admin123
```

### **Data not updating**

- Check if market is open (9:15 AM - 3:30 PM IST)
- Click "🔄 Refresh Data"
- Verify internet connection
- Check access token is valid

---

## 📸 Dashboard Features

### **Market Overview**
```
┌─────────────────────────────────────┐
│  Nifty 50: 24,150.75 (+0.45%)      │
│  ATM Strike: 24150                  │
│  Market: 🟢 OPEN                    │
│  Time to Close: 235 min             │
└─────────────────────────────────────┘
```

### **Options Chain**
```
Strike  | CE LTP | CE Vol | PE LTP | PE Vol
24100   | 180.50 | 25000  | 95.25  | 18000
24150   | 150.00 | 45000  | 125.50 | 42000 ← ATM
24200   | 122.75 | 32000  | 158.00 | 28000
```

### **Performance Metrics**
```
Total Trades: 15
Win Rate: 66.7%
Net P&L: ₹12,450
Profit Factor: 2.1
```

---

## ⚙️ Dashboard vs Trading Engine

| Component | Purpose | Command |
|-----------|---------|---------|
| **Trading Engine** | Executes trades | `python main.py` |
| **Dashboard** | Monitors status | `python run_dashboard.py` |

**Both can run simultaneously!**

---

## 🔒 Security Tips

✅ **DO:**
- Change default password immediately
- Use strong password
- Only access on trusted network
- Logout when done

❌ **DON'T:**
- Use default credentials
- Share login details
- Access over public WiFi
- Expose to internet

---

## 📋 Daily Workflow

```bash
# Every trading morning:

# 1. Generate access token (2 minutes)
python step1_get_login_url.py
python step2_generate_token.py

# 2. Launch dashboard (opens in browser)
python run_dashboard.py

# 3. Login with your credentials

# 4. In another terminal, start trading engine
python main.py

# 5. Monitor dashboard during trading hours

# 6. At end of day: Stop engine (Ctrl+C), close dashboard
```

---

## 💡 Pro Tips

1. **Bookmark the URL:** `http://localhost:8501`
2. **Keep dashboard tab pinned** in browser
3. **Use auto-refresh** instead of manual refresh
4. **Check Performance tab** regularly to track P&L
5. **Monitor Risk tab** to ensure you're within limits
6. **Export data** from database for analysis

---

## 📚 More Information

- **Complete Dashboard Guide:** `DASHBOARD_GUIDE.md`
- **Platform Setup:** `SETUP_GUIDE.md`
- **Full Documentation:** `README.md`

---

## ⚠️ Important Notes

- Dashboard is **READ-ONLY** (displays data, doesn't execute trades)
- Trading engine runs separately (`main.py`)
- Dashboard shows "PAPER TRADING" when paper mode is enabled
- Some data only available during market hours
- Internet required for live data

---

## 🎉 Quick Summary

```bash
# One-time setup
python install_dependencies.py
cp config/config.ini.template config/config.ini
# Edit config.ini with your API credentials

# Daily routine (2 commands)
python step2_generate_token.py  # After getting request_token
python run_dashboard.py         # Launch UI

# Login: admin / admin123 (change it!)
# Monitor your trades in real-time!
```

---

**Enjoy your professional trading dashboard! 📊🚀**

Need help? Check `DASHBOARD_GUIDE.md` for detailed documentation.
