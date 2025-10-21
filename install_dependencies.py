#!/usr/bin/env python3
"""
Dependency Installer & Checker
Run this first to install all required packages
"""

import subprocess
import sys
from pathlib import Path

def check_pip():
    """Check if pip is available"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                      capture_output=True, check=True)
        return True
    except:
        return False

def install_requirements():
    """Install all requirements"""
    req_file = Path(__file__).parent / "requirements.txt"

    if not req_file.exists():
        print(f"❌ Error: requirements.txt not found at {req_file}")
        return False

    print("\n" + "="*80)
    print("NIFTY OPTIONS TRADING PLATFORM - DEPENDENCY INSTALLER")
    print("="*80)

    if not check_pip():
        print("\n❌ Error: pip is not available")
        print("Please install pip first: https://pip.pypa.io/en/stable/installation/")
        return False

    print("\n📦 Installing dependencies from requirements.txt...")
    print("-"*80)

    try:
        # Install requirements
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("\n✅ All dependencies installed successfully!")
            print("-"*80)
            print("\nInstalled packages:")
            print(result.stdout)
            return True
        else:
            print("\n❌ Installation failed!")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"\n❌ Error during installation: {e}")
        return False

def verify_imports():
    """Verify critical imports"""
    print("\n" + "="*80)
    print("VERIFYING INSTALLATION")
    print("="*80)

    critical_packages = [
        ('kiteconnect', 'Zerodha Kite Connect API'),
        ('pandas', 'Data manipulation'),
        ('numpy', 'Numerical computing'),
        ('dotenv', 'Environment variables (python-dotenv)'),
        ('requests', 'HTTP library'),
        ('pytz', 'Timezone handling'),
    ]

    all_ok = True

    for package, description in critical_packages:
        try:
            __import__(package)
            print(f"✅ {package:20} - {description}")
        except ImportError:
            print(f"❌ {package:20} - {description} [MISSING]")
            all_ok = False

    return all_ok

def main():
    # Install dependencies
    success = install_requirements()

    if not success:
        print("\n❌ Installation failed. Please check errors above.")
        sys.exit(1)

    # Verify installation
    print("\n")
    if verify_imports():
        print("\n" + "="*80)
        print("✅ SUCCESS! All dependencies are installed and working")
        print("="*80)
        print("\n📋 NEXT STEPS:")
        print("-"*80)
        print("1. Configure your Kite Connect credentials:")
        print("   cp config/config.ini.template config/config.ini")
        print("   nano config/config.ini  # Add your API key and secret")
        print("\n2. Generate access token:")
        print("   python step1_get_login_url.py")
        print("   python step2_generate_token.py")
        print("\n3. Run the platform:")
        print("   python main.py")
        print("="*80 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("⚠️  Some packages are missing")
        print("="*80)
        print("\nTry installing missing packages manually:")
        print("pip install python-dotenv kiteconnect pandas numpy")
        print("="*80 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
