"""Run the actual windowed executable, wait, and require a fresh success report."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def verify():
    exe = ROOT / "dist/HearliumParentPC/HearliumParentPC.exe"
    internal = exe.parent / "_internal"
    for relative in ("_tkinter.pyd", "tcl86t.dll", "tk86t.dll",
                     "_tcl_data/init.tcl", "_tk_data/tk.tcl"):
        if not (internal / relative).is_file():
            raise RuntimeError(f"Frozen Tk prerequisite missing: {relative}")
    with tempfile.TemporaryDirectory(prefix="hearlium-gui-") as temporary:
        report = Path(temporary) / "gui.json"
        env = dict(os.environ, LOCALAPPDATA=temporary)
        # The PyInstaller runtime hook must override inherited host locations.
        env.update(TCL_LIBRARY=str(Path(temporary) / "absent-tcl"),
                   TK_LIBRARY=str(Path(temporary) / "absent-tk"))
        subprocess.run([str(exe), "--gui-smoke-test", str(report)], env=env,
                       check=True, timeout=90)
        result = json.loads(report.read_text(encoding="utf-8"))
        if result.get("passed") is not True or result.get("frozen") is not True:
            raise RuntimeError("Frozen GUI check did not pass")
        for key in ("tclLibrary", "tkLibrary", "extension"):
            if not Path(result[key]).resolve().is_relative_to(internal.resolve()):
                raise RuntimeError(f"GUI used a host dependency: {key}")
        print(json.dumps(result, indent=2))
        return result


if __name__ == "__main__":
    verify()
