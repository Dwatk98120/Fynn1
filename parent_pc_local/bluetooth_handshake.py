import json
import socket

DEFAULT_PORT = 8000

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def build_handshake(port=DEFAULT_PORT):
    return json.dumps({
        "type": "hearlium_parent_pc",
        "version": 1,
        "host": get_local_ip(),
        "port": int(port),
        "ready": True,
        "transport": "wifi_lan"
    })

if __name__ == "__main__":
    print(build_handshake())
