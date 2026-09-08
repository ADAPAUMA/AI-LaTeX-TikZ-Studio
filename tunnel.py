"""
tunnel.py
---------
Quick public URL tunnel using pyngrok.
Run this to get a shareable link for the local Streamlit app.

Usage:
    python tunnel.py
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pyngrok import ngrok
import time

PORT = 8503

print("=" * 55)
print("  TikZ AI Studio - Public Link Generator")
print("=" * 55)
print(f"\n[*] Tunneling localhost:{PORT} to the internet...\n")

try:
    tunnel = ngrok.connect(PORT, "http")
    public_url = tunnel.public_url

    print(f"[OK] Your public link is ready!\n")
    print(f"     --> {public_url}\n")
    print("     Share this link with anyone.")
    print("     It opens your TikZ AI Studio instantly.\n")
    print("[!]  This link stays active as long as this script runs.")
    print("     Press Ctrl+C to stop.\n")
    print("-" * 55)

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[STOP] Tunnel closed.")
        ngrok.kill()

except Exception as e:
    print(f"\n[ERROR] {e}")
    print("\nIf you see an auth error:")
    print("  1. Visit https://ngrok.com and sign up free")
    print("  2. Copy your authtoken from the dashboard")
    print("  3. Run: python -c \"from pyngrok import ngrok; ngrok.set_auth_token('YOUR_TOKEN')\"")
    print("  4. Then run tunnel.py again\n")
    sys.exit(1)
