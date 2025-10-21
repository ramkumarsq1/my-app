# 🔧 Fix Login Issue - Invalid Credentials

**Quick solutions to fix the "invalid credentials" error**

---

## ⚡ Quick Fix (Most Common)

### **Option 1: Reset to Default Credentials**

```bash
# Delete saved credentials file
rm dashboard/credentials.json

# Restart dashboard
python run_dashboard.py

# Login with defaults:
# Username: admin
# Password: admin123
```

---

## 🔍 Diagnose the Problem

### **Run Authentication Test:**

```bash
python test_auth.py
```

This will:
- ✅ Show current credentials
- ✅ Test password hashing
- ✅ Verify credentials file
- ✅ Create default credentials if missing
- ✅ Test your login

---

## 🛠️ Solutions

### **Solution 1: Use Default Credentials**

Make sure you're typing EXACTLY:
- **Username:** `admin` (lowercase, no spaces)
- **Password:** `admin123` (no spaces)

⚠️ **Common mistakes:**
- Typing "Admin" instead of "admin"
- Extra spaces before/after
- Caps Lock on
- Copy-pasting with extra characters

---

### **Solution 2: Reset Credentials File**

```bash
# Method A: Delete and recreate
rm dashboard/credentials.json
python run_dashboard.py

# Method B: Use test script to recreate
python test_auth.py
# (Will create credentials.json automatically)
```

---

### **Solution 3: Manual Reset from Dashboard**

1. Open dashboard: `http://localhost:8501`
2. On login page, expand **"🔧 Debug Info"**
3. Click **"🔄 Reset to Default Credentials"** button
4. Login with: `admin` / `admin123`

---

### **Solution 4: Create Credentials Manually**

```bash
# Create credentials file manually
cat > dashboard/credentials.json << 'EOF'
{
  "username": "admin",
  "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
}
EOF

# Restart dashboard
python run_dashboard.py
```

---

## 🔐 Password Hash for "admin123"

If you need to verify, the correct SHA256 hash for `admin123` is:
```
240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
```

---

## 🎯 Step-by-Step Fix

### **Complete Reset Process:**

```bash
# Step 1: Stop dashboard (Ctrl+C if running)

# Step 2: Delete credentials
rm dashboard/credentials.json

# Step 3: Test authentication system
python test_auth.py
# This will create default credentials

# Step 4: Restart dashboard
python run_dashboard.py

# Step 5: Open browser
# http://localhost:8501

# Step 6: Login
# Username: admin
# Password: admin123

# Step 7: Change password immediately!
# Click "Change Password" in sidebar
```

---

## 🐛 Debug Mode

The updated auth.py now shows debug information on the login page:

1. **Click "🔧 Debug Info"** on login page
2. You'll see:
   - Current default credentials
   - Stored credentials (if file exists)
   - Username being checked
   - Password hash comparison

This helps identify the exact issue!

---

## 📋 Verification Checklist

Before trying to login, verify:

- [ ] Dashboard is running (`python run_dashboard.py`)
- [ ] Browser is open at `http://localhost:8501`
- [ ] Typing exactly: `admin` (lowercase)
- [ ] Typing exactly: `admin123` (no spaces)
- [ ] Not using Caps Lock
- [ ] Credentials file exists or will be created

---

## 💡 Common Issues

### **Issue: "Invalid username or password"**

**Cause:** Credentials don't match stored hash

**Fix:**
```bash
rm dashboard/credentials.json
python run_dashboard.py
```

### **Issue: Credentials file missing**

**Cause:** File was deleted or never created

**Fix:**
```bash
python test_auth.py  # Creates file automatically
python run_dashboard.py
```

### **Issue: Changed password and forgot it**

**Cause:** Modified credentials and can't remember new password

**Fix:**
```bash
# Reset to defaults
rm dashboard/credentials.json
python run_dashboard.py
# Login with: admin / admin123
```

---

## 🧪 Test Your Login

Run this to test:

```bash
# Test authentication
python test_auth.py

# When prompted, enter:
# Username: admin
# Password: admin123

# Should see: ✅ LOGIN SUCCESSFUL!
```

---

## 📁 Credentials File Location

```
my-app/
└── dashboard/
    └── credentials.json  ← This file stores your credentials
```

**If this file doesn't exist:** Dashboard uses defaults (`admin`/`admin123`)

**If this file exists:** Dashboard uses stored credentials

---

## 🆘 Still Not Working?

### **Last Resort - Complete Reset:**

```bash
# 1. Stop dashboard completely (Ctrl+C)

# 2. Delete everything related to credentials
rm dashboard/credentials.json
rm -rf dashboard/__pycache__

# 3. Clear browser cache
# In browser: Ctrl+Shift+Delete → Clear cache

# 4. Run test script
python test_auth.py

# 5. Start fresh
python run_dashboard.py

# 6. Try login again
# Username: admin
# Password: admin123
```

---

## ✅ Success Indicators

You know it's working when:

1. ✅ `test_auth.py` shows "LOGIN SUCCESSFUL"
2. ✅ Dashboard login page loads
3. ✅ Debug info shows correct credentials
4. ✅ Login button accepts credentials
5. ✅ Dashboard main page appears after login

---

## 🎓 Understanding the System

**How authentication works:**

1. **Password is hashed** using SHA256 (secure)
2. **Hash is stored** in `credentials.json`
3. **Login compares** input hash with stored hash
4. **If match:** Login successful
5. **If no match:** Invalid credentials

**Default credentials:**
- Stored in `auth.py` as fallback
- Used when `credentials.json` doesn't exist
- Always `admin` / `admin123` by default

---

## 📞 Quick Help Commands

```bash
# Check if credentials file exists
ls -la dashboard/credentials.json

# View credentials file
cat dashboard/credentials.json

# Delete credentials
rm dashboard/credentials.json

# Test authentication
python test_auth.py

# Restart dashboard
python run_dashboard.py
```

---

## 🎉 After Successful Login

Once you login successfully:

1. **Change your password immediately!**
   - Click "🔐 Change Password" in sidebar
   - Enter current: `admin123`
   - Set new secure password
   - Confirm new password

2. **Optional: Change username too**
   - In password change form
   - Enter new username
   - Set new password

3. **Logout and test**
   - Click "🚪 Logout"
   - Login with new credentials
   - Verify it works

---

**Need more help?** Check `DASHBOARD_GUIDE.md` or run `python test_auth.py` for diagnostics.
