"""Require the 0.4.18 native alignment and token-evidence checks before packaging."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def verify_frozen():
    exe = ROOT / 'dist/HearliumParentPC/HearliumParentPC.exe'
    with tempfile.TemporaryDirectory(prefix='hearlium-phoneme-') as folder:
        output = Path(folder) / 'checks.json'
        subprocess.run([str(exe), '--verify-phoneme-hotfix', str(output)],
                       env=dict(os.environ, LOCALAPPDATA=folder), check=True, timeout=120)
        report = json.loads(output.read_text(encoding='utf-8'))
        if report.get('passed') is not True or report.get('phonemeHotfixVersion') != '0.4.18':
            raise RuntimeError('Frozen phoneme hotfix check failed')
        if not Path(report['modelDirectory']).resolve().is_relative_to((exe.parent / '_internal').resolve()):
            raise RuntimeError('Alignment engine used an external model')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    if args.frozen:
        verify_frozen()
    else:
        sys.path[:0] = [str(ROOT / 'parent_pc_local'), str(ROOT / 'server'), str(ROOT)]
        from phoneme_hotfix_checks import run_check
        print(json.dumps(run_check(), indent=2))
