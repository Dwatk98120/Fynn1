from __future__ import annotations
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
os.chdir(SERVER)
sys.path.insert(0, str(SERVER))

def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

if __name__ == "__main__":
    import uvicorn
    ip = lan_ip()
    print("")
    print("=" * 68)
    print(" First Sound Helper / Hearlium Parent PC Local Backend")
    print("=" * 68)
    print(f" Android connection address: http://{ip}:8000")
    print(f" Health check:               http://{ip}:8000/health")
    print("")
    print("Keep this window open while the Android app is using analysis.")
    print("The phone and Parent PC must be on the same local network.")
    print("=" * 68)
    print("")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
