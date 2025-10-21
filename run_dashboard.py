#!/usr/bin/env python3
"""
Launch the Nifty Options Trading Dashboard
Web-based UI for monitoring and controlling the trading platform
"""

import subprocess
import sys
from pathlib import Path

def check_streamlit():
    """Check if streamlit is installed"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_dashboard_dependencies():
    """Install dashboard-specific dependencies"""
    print("\n" + "="*80)
    print("Installing dashboard dependencies...")
    print("="*80)

    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "streamlit", "plotly"
        ], check=True)
        print("\n✅ Dashboard dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Error installing dependencies: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("NIFTY OPTIONS TRADING PLATFORM - WEB DASHBOARD")
    print("="*80)

    # Check if streamlit is installed
    if not check_streamlit():
        print("\n⚠️  Streamlit is not installed")
        print("Installing dashboard dependencies...")

        if not install_dashboard_dependencies():
            print("\n❌ Failed to install dependencies")
            print("\nPlease install manually:")
            print("  pip install streamlit plotly")
            sys.exit(1)

    # Get dashboard path
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"

    if not dashboard_path.exists():
        print(f"\n❌ Dashboard not found at: {dashboard_path}")
        sys.exit(1)

    print("\n" + "="*80)
    print("🚀 LAUNCHING DASHBOARD")
    print("="*80)
    print("\n📌 Dashboard will open in your default web browser")
    print("📌 URL: http://localhost:8501")
    print("\n⚠️  To stop the dashboard: Press Ctrl+C in this terminal")
    print("\n" + "="*80 + "\n")

    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.headless", "true",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("Dashboard stopped by user")
        print("="*80 + "\n")
    except Exception as e:
        print(f"\n❌ Error running dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
