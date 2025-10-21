#!/usr/bin/env python3
"""
Step 2: Generate Access Token
Run this script with the request_token from Step 1 to generate access token
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config.config import KITE_API_KEY, KITE_API_SECRET
from kiteconnect import KiteConnect
import configparser

def update_config_file(access_token):
    """Update config.ini with access token"""
    try:
        config_file = Path(__file__).parent / 'config' / 'config.ini'

        if not config_file.exists():
            print(f"\n⚠️  Config file not found at: {config_file}")
            print("Please create it from config.ini.template")
            return False

        config = configparser.ConfigParser()
        config.read(config_file)

        if 'kite' not in config:
            config['kite'] = {}

        config['kite']['access_token'] = access_token

        with open(config_file, 'w') as f:
            config.write(f)

        print(f"\n✓ Config file updated: {config_file}")
        return True

    except Exception as e:
        print(f"\n✗ Error updating config: {e}")
        return False

def main():
    if not KITE_API_KEY or not KITE_API_SECRET:
        print("\n" + "="*80)
        print("ERROR: API Credentials Not Found")
        print("="*80)
        print("\nPlease set your Kite credentials in config/config.ini:")
        print("\n[kite]")
        print("api_key = YOUR_API_KEY")
        print("api_secret = YOUR_API_SECRET")
        print("\nGet these from: https://developers.kite.trade/apps")
        print("="*80 + "\n")
        return

    print("\n" + "="*80)
    print("ZERODHA KITE CONNECT - AUTHENTICATION STEP 2/2")
    print("="*80)
    print("\n📌 STEP 2: GENERATE ACCESS TOKEN")
    print("-"*80)

    # Get request token from user
    request_token = input("\nEnter the request_token from Step 1 (from redirect URL): ").strip()

    if not request_token:
        print("\n✗ Error: No request token provided")
        print("\nPlease run 'python step1_get_login_url.py' first to get request_token")
        return

    print("\n⏳ Generating access token...")

    # Initialize Kite
    kite = KiteConnect(api_key=KITE_API_KEY)

    try:
        # Generate session
        data = kite.generate_session(request_token, api_secret=KITE_API_SECRET)
        access_token = data["access_token"]
        user_id = data.get("user_id", "")
        user_name = data.get("user_name", "")

        print("\n" + "="*80)
        print("✅ SUCCESS! ACCESS TOKEN GENERATED")
        print("="*80)
        print(f"\nUser: {user_name} ({user_id})")
        print(f"\nAccess Token: {access_token}")
        print("\n" + "-"*80)
        print("⚠️  IMPORTANT NOTES:")
        print("-"*80)
        print("1. This access token is valid until end of trading day (3:30 PM)")
        print("2. You'll need to regenerate it daily (run these scripts again)")
        print("3. Keep it secure - it has full access to your trading account")
        print("4. For daily automation, consider using TOTP for auto-login")
        print("\n" + "-"*80)
        print("SAVING TOKEN TO CONFIG...")
        print("-"*80)

        # Try to update config file
        if update_config_file(access_token):
            print("\n✅ SETUP COMPLETE!")
            print("\nYou can now run the trading platform:")
            print("   python main.py")
        else:
            print("\n⚠️  Manual Setup Required")
            print("\nAdd this to your config/config.ini:")
            print(f"\n[kite]")
            print(f"access_token = {access_token}")
            print("\nOr set environment variable:")
            print(f"export KITE_ACCESS_TOKEN={access_token}")

        print("\n" + "="*80)
        print("🎉 You're all set! Happy trading!")
        print("="*80 + "\n")

    except Exception as e:
        print("\n" + "="*80)
        print("✗ ERROR GENERATING ACCESS TOKEN")
        print("="*80)
        print(f"\nError: {e}")
        print("\n" + "-"*80)
        print("COMMON ISSUES & SOLUTIONS:")
        print("-"*80)
        print("1. 'Invalid request_token'")
        print("   → Request token is single-use only")
        print("   → Run step1_get_login_url.py again to get a new one")
        print("\n2. 'request_token has expired'")
        print("   → Request tokens expire in a few minutes")
        print("   → Get a fresh token from step 1")
        print("\n3. 'Invalid api_secret'")
        print("   → Check your API secret in config/config.ini")
        print("   → Verify it matches your Kite Connect app settings")
        print("\n4. 'Incorrect api_key'")
        print("   → Verify API key in config/config.ini")
        print("   → Check it from: https://developers.kite.trade/apps")
        print("="*80 + "\n")

if __name__ == "__main__":
    main()
