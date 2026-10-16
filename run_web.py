"""Runner script for the CivicPulse AI Full-Fledged Web Application.

Usage:
    python run_web.py
"""

import sys
import uvicorn

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 65)
    print("  CIVICPULSE AI -- SMART CITY DISPATCH & CITIZEN PORTAL")
    print("=" * 65)
    print(f"  [*] Website URL:          http://localhost:{port}")
    print("  [*] Citizen Public View:  No login required (Direct reporting)")
    print("  [*] Govt Officer Login:   officer@smartcity.gov / password123")
    print("  [*] Field Worker Login:   worker@smartcity.gov  / password123")
    print("=" * 65)
    print(f"  Starting Uvicorn web server on port {port}...\n")

    uvicorn.run("web.server:app", host="0.0.0.0", port=port, reload=False)
