"""Fail-closed installer-only audit of pinned offline speech build packages.

Run from .installer_venv/Scripts/python.exe after the normal dependency stage.
The --repair option only installs known, pinned packages into THAT isolated
environment. It never modifies a user's global Python or any audio evidence.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
from importlib import metadata, util
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class Dependency:
    distribution: str
    module: str
    version: str
    extra_pip_args: tuple[str, ...] = ("--only-binary=:all:",)

    @property
    def pinned_spec(self) -> str:
        return f"{self.distribution}=={self.version}"


# Match the pinned packages in BUILD_HEARLIUM_INSTALLER.bat and
# server/requirements-word-asr.txt. No dynamic or unreviewed pip arguments.
REQUIRED = (
    Dependency("pyinstaller", "PyInstaller", "6.16.0"),
    Dependency("fastapi", "fastapi", "0.115.6"),
    Dependency("uvicorn", "uvicorn", "0.34.0"),
    Dependency("python-multipart", "multipart", "0.0.20"),
    Dependency("numpy", "numpy", "1.26.4"),
    Dependency("soundfile", "soundfile", "0.13.1"),
    Dependency("sounddevice", "sounddevice", "0.5.2"),
    Dependency("requests", "requests", "2.32.3"),
    Dependency("transformers", "transformers", "4.49.0"),
    Dependency("torch", "torch", "2.6.0"),
    Dependency("silero-vad", "silero_vad", "6.2.3"),
    Dependency("nltk", "nltk", "3.9.1"),
    Dependency("inflect", "inflect", "7.5.0"),
    Dependency("distance", "distance", "0.1.3",
               ("--no-build-isolation", "--no-use-pep517")),
    Dependency("g2p-en", "g2p_en", "2.1.0",
               ("--only-binary=g2p-en", "--no-deps")),
    Dependency("av", "av", "13.1.0"),
    Dependency("ctranslate2", "ctranslate2", "4.4.0"),
    Dependency("faster-whisper", "faster_whisper", "1.1.1"),
    Dependency("pytest", "pytest", "8.4.2"),
    Dependency("pocketsphinx", "pocketsphinx", "5.0.4"),
)


def _installed(dep: Dependency) -> bool:
    try:
        current_version = metadata.version(dep.distribution)
        module_present = util.find_spec(dep.module) is not None
    except (metadata.PackageNotFoundError, ImportError, ValueError,
            ModuleNotFoundError):
        return False
    return module_present and current_version == dep.version


def audit(*, repair: bool, dependencies=REQUIRED) -> bool:
    """Return True only if every audited package resolves at its pinned version."""
    if repair and Path(sys.prefix).name.lower() != ".installer_venv":
        print("ERROR: Automatic dependency repair is permitted only inside "
              ".installer_venv; global Python will not be changed.", flush=True)
        return False

    print("Auditing required build modules in:", sys.executable, flush=True)
    for dep in dependencies:
        if _installed(dep):
            print("OK:", dep.pinned_spec, flush=True)
            continue
        print("MISSING OR UNPINNED:", dep.pinned_spec,
              "(module:", dep.module + ")", flush=True)
        if not repair:
            return False

        command = [sys.executable, "-m", "pip", "install",
                   *dep.extra_pip_args, dep.pinned_spec]
        print("Repairing isolated build package:", dep.pinned_spec, flush=True)
        try:
            subprocess.run(command, check=True)
        except (subprocess.CalledProcessError, OSError) as exc:
            print("ERROR: Required dependency repair failed:",
                  dep.pinned_spec, type(exc).__name__, flush=True)
            return False

        importlib.invalidate_caches()
        if not _installed(dep):
            print("ERROR: Package remains missing or unpinned after install:",
                  dep.pinned_spec, flush=True)
            return False

    print("All required build dependencies are present at pinned versions.",
          flush=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair", action="store_true",
                        help="repair missing pinned packages in .installer_venv only")
    args = parser.parse_args()
    return 0 if audit(repair=args.repair) else 1


if __name__ == "__main__":
    raise SystemExit(main())
