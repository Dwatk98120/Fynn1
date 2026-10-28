"""Require the synthetic same-ID legacy-alias storage check in the frozen EXE."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    if args.frozen:
        with tempfile.TemporaryDirectory(prefix='hearlium-alias-') as folder:
            output = Path(folder) / 'check.json'
            env = dict(os.environ, LOCALAPPDATA=folder, FSH_RECORDINGS_DIR=str(Path(folder) / 'recordings'))
            subprocess.run([str(ROOT / 'dist/HearliumParentPC/HearliumParentPC.exe'),
                            '--verify-legacy-alias', str(output)], env=env, check=True, timeout=90)
            report = json.loads(output.read_text(encoding='utf-8'))
    else:
        sys.path[:0] = [str(ROOT / 'parent_pc_local'), str(ROOT / 'server'), str(ROOT)]
        from legacy_alias_checks import run_check
        report = run_check()
    if (report.get('passed') is not True
            or report.get('legacyAliasHotfixVersion') != '0.4.19'
            or report.get('receiptConflictsRejected') is not True):
        raise RuntimeError('Legacy alias frozen check failed')
    print(json.dumps(report, indent=2))
