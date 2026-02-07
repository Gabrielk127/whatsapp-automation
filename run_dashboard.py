"""Script to run the monitoring dashboard."""

import subprocess
import sys
from pathlib import Path

def main():
    """Start the dashboard server."""
    dashboard_dir = Path(__file__).parent / "src" / "dashboard"
    
    print("🚀 Starting WhatsApp Automation Dashboard...")
    print(f"📂 Dashboard directory: {dashboard_dir}")
    print("🌐 Dashboard will be available at: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Run uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.dashboard.api:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
