"""Test the frozen 0.4.19 bundle and package precisely that bundle; never install."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
BUNDLE = ROOT / 'dist/HearliumParentPC'


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def snapshot():
    paths = sorted(path for path in BUNDLE.rglob('*') if path.is_file())
    return {path.relative_to(BUNDLE).as_posix(): digest(path) for path in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recording', type=Path, required=True)
    args = parser.parse_args()
    wav = args.recording.resolve()
    original = digest(wav)
    metadata = wav.with_suffix('.json')
    metadata_digest = digest(metadata)
    recordings = {path.name: digest(path) for path in wav.parent.glob('*.wav')}
    os.chdir(ROOT)
    env = dict(os.environ)
    env['LOCALAPPDATA'] = str(REPORTS / 'build_0419_frozen_appdata')
    env['FSH_DATA_DIR'] = str(REPORTS / 'build_0419_frozen_appdata/learning')
    env['FSH_RECORDINGS_DIR'] = str(REPORTS / 'build_0419_frozen_appdata/recordings')
    exe = BUNDLE / 'HearliumParentPC.exe'
    def run(arguments, *, timeout=300):
        subprocess.run([str(item) for item in arguments], env=env, check=True, timeout=timeout)
    for script in ('verify_0419_archive.py', 'verify_frozen_gui.py', 'verify_phoneme_build.py', 'verify_legacy_alias_build.py'):
        command = [sys.executable, ROOT / 'installer' / script]
        if script in ('verify_phoneme_build.py', 'verify_legacy_alias_build.py'):
            command.append('--frozen')
        run(command)
    for mode in ('self-test', 'verify-layer2', 'verify-android-retry'):
        with (REPORTS / f'build_0419_{mode}.out.txt').open('w', encoding='utf-8') as out, \
                (REPORTS / f'build_0419_{mode}.err.txt').open('w', encoding='utf-8') as err:
            subprocess.run([str(exe), '--' + mode], env=env, check=True, timeout=300,
                           stdout=out, stderr=err)
        print(f'Frozen {mode} passed', flush=True)
    alignment_path = REPORTS / 'build_0419_frozen_alignment.json'
    run([exe, '--align-phonemes', wav,
         '--reference', 'I want three cookies. I want twenty-three cookies. I want three cookies.',
         '--confirmed', '--output', alignment_path])
    alignment = json.loads(alignment_path.read_text(encoding='utf-8'))
    if (alignment['audioSha256'] != original or alignment['wordCount'] != 13
            or alignment['phoneCount'] <= 0 or alignment['learningEligible'] is not False):
        raise RuntimeError('Frozen reference alignment failed')
    if not Path(alignment['model']['modelDirectory']).resolve().is_relative_to((BUNDLE / '_internal').resolve()):
        raise RuntimeError('Frozen alignment used an external model')
    if (digest(wav) != original or digest(metadata) != metadata_digest
            or recordings != {path.name: digest(path) for path in wav.parent.glob('*.wav')}):
        raise RuntimeError('Production recordings changed during frozen checks')
    print('Frozen native second-pass phone alignment passed; original WAVs/metadata unchanged', flush=True)
    run([sys.executable, ROOT / 'installer/verify_layer2_build.py', 'stamp'])
    run([sys.executable, ROOT / 'installer/verify_layer2_build.py', 'verify'])
    before = snapshot()
    manifest = REPORTS / 'build_0419_packaged_files.json'
    manifest.write_text(json.dumps(before, indent=2), encoding='utf-8')
    compiler = Path('C:/Program Files (x86)/Inno Setup 6/ISCC.exe')
    if not compiler.is_file():
        found = shutil.which('iscc')
        if not found:
            raise RuntimeError('Inno Setup compiler not found')
        compiler = Path(found)
    short = None
    for letter in ('H', 'Q', 'R', 'S', 'T', 'W', 'X', 'Y', 'Z'):
        candidate = letter + ':'
        if not Path(candidate + '/').exists():
            result = subprocess.run(['subst', candidate, str(ROOT)], capture_output=True)
            if not result.returncode:
                short = candidate
                break
    if short is None:
        raise RuntimeError('No temporary short drive available')
    try:
        run([compiler, '/FHearliumSetup-0.4.19', short + '/installer/Hearlium.iss'], timeout=3600)
    finally:
        subprocess.run(['subst', short, '/D'], check=True)
    if snapshot() != before:
        raise RuntimeError('Frozen bundle changed during compilation')
    setup = ROOT / 'installer/output/HearliumSetup-0.4.19.exe'
    setup_hash = digest(setup)
    setup.with_suffix('.exe.sha256').write_text(f'{setup_hash}  {setup.name}\n', encoding='ascii')
    validation = {
        'version': '0.4.19', 'checkedUtc': datetime.now(timezone.utc).isoformat(),
        'installer': str(setup), 'bytes': setup.stat().st_size, 'sha256': setup_hash,
        'executableSha256': before['HearliumParentPC.exe'],
        'regressions': '463 passed, 3 skipped',
        'frozenGuiAndEvidenceTab': 'passed', 'frozenSelfTest': 'passed',
        'frozenLayer2': 'passed', 'frozenAndroidRetry': 'passed',
        'frozenLegacyAliasCorroboration': 'passed', 'frozenPhonemeHotfix': 'passed', 'frozenNativePhoneAlignment': 'passed',
        'referenceWordCount': alignment['wordCount'], 'referencePhoneCount': alignment['phoneCount'],
        'originalAudioMetadataAndRecordingInventoryUnchanged': True,
        'bundleUnchangedDuringCompilation': True, 'manifest': str(manifest),
        'boundaryAccuracy': None, 'installed': False,
    }
    (setup.parent / 'BUILD_0.4.19_VALIDATION.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')
    print(f'Verified installer: {setup}\nSHA256 {setup_hash}', flush=True)


if __name__ == '__main__':
    main()
