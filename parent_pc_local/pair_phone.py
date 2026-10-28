from __future__ import annotations

import os
import socket
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import sys
import urllib.request

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parents[1]
API_SCRIPT = ROOT / "parent_pc_local" / "start_parent_pc_server.py"
BT_EXE = ROOT / "HearliumBluetoothService.exe" if FROZEN else ROOT / "parent_pc_local" / "bluetooth_service" / "bin" / "Release" / "net8.0-windows10.0.19041.0" / "win-x64" / "publish" / "HearliumBluetoothService.exe"

def server_healthy():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False

class PairPhone(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hearlium — Pair Phone")
        self.geometry("560x470")
        self.resizable(False, False)
        self.api_proc = None
        self.bt_proc = None

        tk.Label(self, text="Pair Your Phone", font=("Segoe UI", 24, "bold")).pack(pady=(22, 6))
        tk.Label(
            self,
            text="One simple setup. Hearlium handles the technical connection details.",
            font=("Segoe UI", 10),
            wraplength=500
        ).pack(pady=(0, 18))

        self.status = tk.StringVar(value="Ready to pair")
        tk.Label(self, textvariable=self.status, font=("Segoe UI", 12, "bold")).pack(pady=6)

        card = tk.Frame(self, bd=1, relief="groove")
        card.pack(fill="x", padx=28, pady=12)

        self.ip = self.local_ip()
        tk.Label(card, text="Parent PC", font=("Segoe UI", 11, "bold")).pack(pady=(12, 2))
        tk.Label(card, text=f"Local connection: {self.ip}:8000", font=("Segoe UI", 10)).pack(pady=2)
        tk.Label(
            card,
            text="You normally do not need to type this into the phone.",
            font=("Segoe UI", 9)
        ).pack(pady=(2, 12))

        tk.Button(
            self,
            text="PAIR PHONE",
            font=("Segoe UI", 14, "bold"),
            width=24,
            height=2,
            command=self.start_pairing
        ).pack(pady=(14, 10))

        tk.Label(
            self,
            text=(
                "On Android: Parent PC Connection → Easy Connect → Find Parent PC.\n"
                "Choose this computer once. Hearlium will remember it."
            ),
            justify="center",
            wraplength=500,
            font=("Segoe UI", 10)
        ).pack(pady=8)

        tk.Button(self, text="Open Windows Bluetooth Settings", command=self.open_bt_settings).pack(pady=6)

    def local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start_pairing(self):
        self.status.set("Starting Parent PC connection services…")
        try:
            # Reuse the server launched by the main Hearlium window.
            # A frozen installation does not contain a developer .venv.
            if not server_healthy():
                if FROZEN:
                    self.api_proc = subprocess.Popen(
                        [sys.executable, "--server"], cwd=str(ROOT),
                        creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
                    )
                else:
                    python = ROOT / ".venv" / "Scripts" / "python.exe"
                    if not python.exists():
                        python = Path(sys.executable)
                    self.api_proc = subprocess.Popen(
                        [str(python), str(API_SCRIPT)], cwd=str(ROOT),
                        creationflags=(subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0),
                    )
                import time
                for _ in range(20):
                    if server_healthy():
                        break
                    time.sleep(0.5)
                if not server_healthy():
                    raise RuntimeError("The local speech server did not become ready. Open Hearlium and select Start Parent PC, then try again.")

            if BT_EXE.exists() and (self.bt_proc is None or self.bt_proc.poll() is not None):
                self.bt_proc = subprocess.Popen([str(BT_EXE)], cwd=str(ROOT))

            if BT_EXE.exists():
                self.status.set("Ready — find this PC from the phone")
            else:
                self.status.set("API ready — Bluetooth helper still needs to be built")
                messagebox.showinfo(
                    "Bluetooth helper",
                    "The local Parent PC server is running.\n\n"
                    "Bluetooth pairing is not available in this installation. "
                    "Rebuild the Windows installer with the .NET 8 SDK to include the Bluetooth service. "
                    "You can still connect over local Wi-Fi using the displayed address."
                )
        except Exception as exc:
            self.status.set("Could not start pairing")
            messagebox.showerror("Pair Phone", str(exc))

    def open_bt_settings(self):
        try:
            os.startfile("ms-settings:bluetooth")
        except Exception as exc:
            messagebox.showerror("Bluetooth Settings", str(exc))

if __name__ == "__main__":
    PairPhone().mainloop()
