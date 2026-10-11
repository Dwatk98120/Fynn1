# Parent PC Python requirement

This build intentionally uses Python 3.12 for the Parent PC virtual environment.

`setup_and_start.bat` now:
- checks that Python 3.12 is installed through the Windows `py` launcher
- detects an existing `.venv`
- automatically removes/rebuilds the environment if it was created with another Python version
- creates the new environment with `py -3.12 -m venv .venv`
- installs the server requirements
- starts the local Parent PC backend

This prevents a newer unsupported Python installation (such as Python 3.15 prerelease) from being used accidentally.
