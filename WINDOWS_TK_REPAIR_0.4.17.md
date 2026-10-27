# Windows 0.4.17 Tk packaging repair

The failing frozen build reports `tkinter` missing in
`build/HearliumParentPC/warn-HearliumParentPC.txt`. The spec has no exclusions;
the launcher and GUI modules already import Tk. This is not a pip dependency.

The exact PyInstaller interpreter is `.installer_venv/Scripts/python.exe`,
Python 3.12.10 based on the full Python312 installation recorded in
`.installer_venv/pyvenv.cfg`. Both `tkinter` and `_tkinter.pyd` are installed.
In the restricted build sandbox, creating a Tcl interpreter fails to load
`init.tcl`. With the same interpreter outside that sandbox, Tcl and Tk 8.6.15
initialize successfully and a hidden window can be created and destroyed.
PyInstaller discovers 926 Tcl/Tk data files there.

PyInstaller 6.16.0's `pre_find_module_path/hook-tkinter.py` explicitly removes
Tk from its search when `tcltk_info.available` is false. Its discovery helper
returns unavailable when `tkinter.Tcl()` fails. This reproduces the mechanism
that produces the missing Tk application despite installed Python modules.
The build must have access to the full Python installation's Tcl scripts.
No Python installation repair or pip installation of tkinter is needed here.

The spec now fails closed before collection if Tk discovery fails and explicitly
includes the Tk modules used by the interface. Standard PyInstaller Tk hooks
collect the native extension, Tcl/Tk DLLs and data, and set the frozen data paths.

`installer/verify_tk_build.py` checks the exact interpreter, real hidden Tk
window, GUI module import, and isolated PyInstaller discovery.
`installer/verify_frozen_gui.py` launches the actual windowed EXE, waits for it,
requires a fresh success report, verifies bundled native/data files and confirms
the reported Tcl/Tk/extension paths stay inside `_internal`. It deliberately
supplies invalid inherited Tcl paths to verify the runtime hook replaces them.
Both the full builder and compiler-only integrity guard require this test.
The ordinary frozen self-test also exercises Tk now.

A clean freeze uses separate `reports/tk_repair_build` and
`reports/tk_repair_dist` directories, with the existing build environment and
unchanged pinned dependencies/offline models. The old distribution is preserved
as `dist/HearliumParentPC-before-TkRepair` before promoting the rebuilt bundle.
The dependency consistency check passes. Regression output is recorded in
`reports/tk_repair_regression.txt` (356 passed, 3 skipped).

`installer/finish_tk_repair.ps1` checks the frozen GUI, server self-test, Layer 2,
Android retry and legacy checksum reanalysis archive markers. It stamps the
tested executable, hashes every distribution file before and after Inno
compilation and requires identical snapshots. Inno's existing recursive Files
mapping packages that exact distribution. The manifest is
`reports/tk_repair_packaged_files.json`; compiler/test output is
`reports/tk_repair_installer.log` and the installer validation record is
`installer/output/BUILD_0.4.17_TK_REPAIR_VALIDATION.json`.

Corrected output: `installer/output/HearliumSetup-0.4.17-TkRepair.exe`.
This retains application version 0.4.17 and its installation identity.
No installer is automatically run. Smoke tests use isolated temporary/workspace
application data; recordings, metadata, historical results and reanalysis
implementation are not changed.

For future full builds, `HEARLIUM_BASE_PYTHON` can name a full Python 3.12
executable when the `py -3.12` launcher is unavailable. Run the build in a context
that can read its Tcl/Tk installation. The new prerequisite check rejects an
inaccessible or incomplete Tk installation before freezing.
