#!/usr/bin/env python3
"""
Test authentication system
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import hashlib
import json

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Default credentials
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

print("\n" + "="*60)
print("AUTHENTICATION SYSTEM TEST")
print("="*60)

print("\n1. Default Credentials:")
print(f"   Username: {DEFAULT_USERNAME}")
print(f"   Password: {DEFAULT_PASSWORD}")

print("\n2. Password Hash:")
password_hash = hash_password(DEFAULT_PASSWORD)
print(f"   Hash: {password_hash}")

print("\n3. Credentials File:")
creds_file = Path(__file__).parent / "dashboard" / "credentials.json"
print(f"   Path: {creds_file}")
print(f"   Exists: {creds_file.exists()}")

if creds_file.exists():
    with open(creds_file, 'r') as f:
        stored_creds = json.load(f)
    print(f"   Stored Username: {stored_creds.get('username', 'N/A')}")
    print(f"   Stored Hash: {stored_creds.get('password_hash', 'N/A')}")

    print("\n4. Verification:")
    print(f"   Username Match: {DEFAULT_USERNAME == stored_creds.get('username', '')}")
    print(f"   Password Match: {password_hash == stored_creds.get('password_hash', '')}")
else:
    print("   Status: No saved credentials (will use defaults)")
    print("\n4. Creating default credentials file...")

    # Create credentials file
    creds_file.parent.mkdir(parents=True, exist_ok=True)
    default_creds = {
        "username": DEFAULT_USERNAME,
        "password_hash": password_hash
    }

    with open(creds_file, 'w') as f:
        json.dump(default_creds, f, indent=2)

    print(f"   ✅ Created: {creds_file}")
    print(f"   Username: {DEFAULT_USERNAME}")
    print(f"   Password: {DEFAULT_PASSWORD}")

print("\n5. Test Login:")
test_user = input("   Enter username to test (default: admin): ").strip() or "admin"
test_pass = input("   Enter password to test (default: admin123): ").strip() or "admin123"

test_hash = hash_password(test_pass)

# Load credentials
if creds_file.exists():
    with open(creds_file, 'r') as f:
        creds = json.load(f)

    username_ok = test_user == creds["username"]
    password_ok = test_hash == creds["password_hash"]

    print(f"\n   Username '{test_user}': {'✅ MATCH' if username_ok else '❌ NO MATCH'}")
    print(f"   Password: {'✅ MATCH' if password_ok else '❌ NO MATCH'}")

    if username_ok and password_ok:
        print("\n   ✅ LOGIN SUCCESSFUL!")
    else:
        print("\n   ❌ LOGIN FAILED!")
        if not username_ok:
            print(f"      Expected username: {creds['username']}")
        if not password_ok:
            print("      Password hash mismatch")
else:
    print("   ❌ Credentials file not found!")

print("\n" + "="*60)
print("\nTo reset credentials, delete: dashboard/credentials.json")
print("Then restart the dashboard to use defaults.")
print("="*60 + "\n")
