"""Fail closed on unavailable Tk, including PyInstaller's isolated discovery."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "parent_pc_local"))
from gui_smoke_check import run_check

if __name__ == "__main__":
    try:
        report = run_check()
        from PyInstaller.utils.hooks.tcl_tk import tcltk_info
        if not tcltk_info.available or not tcltk_info.data_files:
            raise RuntimeError("PyInstaller cannot discover Tcl/Tk data")
        report["pyinstallerTkDataFiles"] = len(tcltk_info.data_files)
        print(json.dumps(report, indent=2))
    except Exception:
        print("Tk prerequisite failed. Use a full Python 3.12 installation with Tcl/Tk; "
              "check build-process access to its Tcl files. Do not pip install tkinter.",
              file=sys.stderr)
        raise
