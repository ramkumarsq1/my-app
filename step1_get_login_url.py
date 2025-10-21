#!/usr/bin/env python3
"""
Step 1: Get Kite Connect Login URL
Run this script to get the login URL for Zerodha authentication
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config.config import KITE_API_KEY
from kiteconnect import KiteConnect

def main():
    if not KITE_API_KEY:
        print("\n" + "="*80)
        print("ERROR: API Key Not Found")
        print("="*80)
        print("\nPlease set your Kite API key in config/config.ini:")
        print("\n[kite]")
        print("api_key = YOUR_API_KEY_HERE")
        print("\nGet your API key from: https://developers.kite.trade/apps")
        print("="*80 + "\n")
        return

    # Initialize Kite
    kite = KiteConnect(api_key=KITE_API_KEY)
    login_url = kite.login_url()

    print("\n" + "="*80)
    print("ZERODHA KITE CONNECT - AUTHENTICATION STEP 1/2")
    print("="*80)
    print("\n📌 STEP 1: LOGIN TO ZERODHA")
    print("-"*80)
    print("\n1. Open this URL in your browser:\n")
    print(f"   {login_url}\n")
    print("2. Login with your Zerodha credentials (User ID + Password + 2FA)")
    print("\n3. After successful login, you'll be redirected to a URL like:")
    print("   http://127.0.0.1/?request_token=XXXXXXXXX&action=login&status=success")
    print("\n4. ⚠️  COPY the 'request_token' value from the redirected URL")
    print("   (The long string after 'request_token=' and before '&')")
    print("\n5. Keep the browser window open (you'll need the token in next step)")
    print("\n" + "="*80)
    print("NEXT: Run 'python step2_generate_token.py' with your request_token")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
