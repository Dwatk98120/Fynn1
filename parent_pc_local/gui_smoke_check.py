"""Exercise Tk without starting servers or opening caregiver data."""
import sys


def run_check():
    import tkinter as tk
    import _tkinter
    from tkinter import ttk, filedialog, messagebox, font
    # Import the real entry module as well as the standard library widgets.
    from hearlium_parent_pc_gui import HearliumParentPC
    root = tk.Tk()
    root.withdraw()
    try:
        widget = ttk.Frame(root)
        widget.destroy()
        from direct_recording import DirectRecorder
        from types import SimpleNamespace
        tab = ttk.Frame(root)
        stub = SimpleNamespace(refresh_evidence=lambda: None, align_confirmed_words=lambda: None)
        DirectRecorder._build_evidence_tab(stub, tab)
        if not stub.evidence_box.winfo_exists():
            raise RuntimeError('Recording evidence tab did not initialize')
        tab.destroy()
        root.update_idletasks()
        return {
            "passed": True, "frozen": bool(getattr(sys, "frozen", False)),
            "python": sys.executable, "tkinter": tk.__file__,
            "extension": _tkinter.__file__,
            "tcl": root.tk.call("info", "patchlevel"),
            "tk": root.tk.call("package", "provide", "Tk"),
            "tclLibrary": root.tk.call("info", "library"),
            "tkLibrary": root.tk.eval("set tk_library"),
        }
    finally:
        root.destroy()
