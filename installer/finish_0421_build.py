"""Verify and package a freshly frozen 0.4.21 bundle without installing it."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'dist/HearliumParentPC'
REPORTS = ROOT / 'reports'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def snapshot():
    paths = sorted(p for p in BUNDLE.rglob('*') if p.is_file())
    with ThreadPoolExecutor(max_workers=8) as pool:
        hashes = pool.map(digest, paths)
        return {p.relative_to(BUNDLE).as_posix(): h for p, h in zip(paths, hashes)}


def verify_package(before, passed, skipped):
    if snapshot() != before:
        raise RuntimeError('Frozen bundle changed during installer compilation')
    setup = ROOT / 'installer/output/HearliumSetup-0.4.21.exe'
    proof = {'version': '0.4.21', 'checkedUtc': datetime.now(timezone.utc).isoformat(),
             'installer': setup.name, 'bytes': setup.stat().st_size, 'sha256': digest(setup),
             'executableSha256': before['HearliumParentPC.exe'], 'sourceTests': {'passed': passed, 'skipped': skipped},
             'frozenChecks': ['archive', 'gui', 'phoneme', 'receipt_integrity', 'self-test',
                              'verify-layer2', 'verify-android-retry', 'stamp', 'verify_stamp'],
             'frozenOfflinePronunciation': True, 'storedCopyProtocolPresent': True,
             'bundleUnchangedDuringCompilation': True, 'installed': False,
             'installedDeviceAcceptance': 'pending', 'privateAudioUsed': False,
             'recognitionOrAlignmentAccuracyValidated': False}
    setup.with_suffix('.exe.sha256').write_text(proof['sha256'] + '  ' + setup.name + '\n', encoding='ascii')
    (setup.parent / 'BUILD_0.4.21_VALIDATION.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps(proof, indent=2), flush=True)


def main():
    os.chdir(ROOT)
    REPORTS.mkdir(exist_ok=True)
    env = dict(os.environ, LOCALAPPDATA=str(REPORTS / 'build_0421_frozen_appdata'),
               APPDATA=str(REPORTS / 'build_0421_frozen_appdata'),
               FSH_DATA_DIR=str(REPORTS / 'build_0421_frozen_appdata/learning'),
               FSH_RECORDINGS_DIR=str(REPORTS / 'build_0421_frozen_appdata/recordings'),
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    suites = ET.parse(REPORTS / '0421_pytest.xml').getroot().findall('testsuite')
    if not suites or any(int(s.get('failures', 0)) or int(s.get('errors', 0)) for s in suites):
        raise RuntimeError('Passing 0.4.21 source test report required')
    skipped = sum(int(s.get('skipped', 0)) for s in suites)
    passed = sum(int(s.get('tests', 0)) for s in suites) - skipped
    if sys.argv[1:] == ['--verify-existing']:
        # Resume only the read-only final verification of a successful compiler
        # run. Require the exact tested source/EXE stamp and full pre-compile
        # bundle snapshot; all files are rehashed before any proof is issued.
        compiler_log = (REPORTS / '0421_inno.log').read_text(encoding='utf-8')
        if 'Successful compile' not in compiler_log:
            raise RuntimeError('A successful compiler log is required')
        stamp = json.loads((BUNDLE / 'layer2_build_integrity.json').read_text())
        if stamp.get('testedFrozenExecutable') is not True:
            raise RuntimeError('A tested frozen build stamp is required')
        for name, expected in stamp['filesSha256'].items():
            if digest(ROOT / name) != expected:
                raise RuntimeError('Tested source or EXE changed: ' + name)
        before = json.loads((REPORTS / '0421_packaged_files_sha256.json').read_text())
        if before['HearliumParentPC.exe'] != digest(BUNDLE / 'HearliumParentPC.exe'):
            raise RuntimeError('Executable changed since compiler input snapshot')
        verify_package(before, passed, skipped)
        return
    if sys.argv[1:]:
        raise RuntimeError('Unknown arguments')
    def run(args, name, timeout=300):
        print('Running', name, flush=True)
        with (REPORTS / ('0421_' + name + '.log')).open('w', encoding='utf-8') as log:
            subprocess.run([str(a) for a in args], env=env, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=timeout)
        print('Passed', name, flush=True)
    exe = BUNDLE / 'HearliumParentPC.exe'
    bluetooth = ROOT / 'parent_pc_local/bluetooth_service/bin/Release/net8.0-windows10.0.22000.0/win-x64/publish/HearliumBluetoothService.exe'
    shutil.copy2(bluetooth, BUNDLE / bluetooth.name)
    run([sys.executable, 'installer/verify_0421_archive.py'], 'archive')
    run([sys.executable, 'installer/verify_frozen_gui.py'], 'gui')
    run([sys.executable, 'installer/verify_phoneme_build.py', '--frozen'], 'phoneme')
    run([sys.executable, 'installer/verify_legacy_alias_build.py', '--frozen'], 'receipt_integrity')
    for mode in ('self-test', 'verify-layer2', 'verify-android-retry'):
        run([exe, '--' + mode], mode)
    run([sys.executable, 'installer/verify_layer2_build.py', 'stamp'], 'stamp')
    run([sys.executable, 'installer/verify_layer2_build.py', 'verify'], 'verify_stamp')
    before = snapshot()
    (REPORTS / '0421_packaged_files_sha256.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    compiler = Path('C:/Program Files (x86)/Inno Setup 6/ISCC.exe')
    if not compiler.is_file():
        raise RuntimeError('Inno Setup 6 compiler required')
    short = None
    for letter in ('H', 'Q', 'R', 'S', 'T', 'W', 'X', 'Y', 'Z'):
        if not Path(letter + ':/').exists():
            candidate = letter + ':'
            if subprocess.run(['subst', candidate, str(ROOT)], capture_output=True).returncode == 0:
                short = candidate
                break
    if short is None:
        raise RuntimeError('Temporary short build drive unavailable')
    try:
        run([compiler, '/FHearliumSetup-0.4.21', short + '/installer/Hearlium.iss'], 'inno', timeout=3600)
    finally:
        subprocess.run(['subst', short, '/D'], check=True)
    verify_package(before, passed, skipped)


if __name__ == '__main__':
    main()
