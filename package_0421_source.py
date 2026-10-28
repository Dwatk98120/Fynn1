"""Prepare an allowlisted source-only 0.4.21 handoff; never copy runtime data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
ADDED = ('AGENTS.md', '.github/workflows/verify-parent-pc-source.yml',
         'BUILD_0.4.21_README.txt', 'GITHUB_0.4.21_UPLOAD.md', 'TEST_RESULTS_0.4.21.md',
         'SOURCE_RELEASE_0.4.21_VERIFICATION.json', 'package_0421_source.py',
         'installer/finish_0421_build.py', 'installer/verify_0421_archive.py',
         'server/tests/test_release_0420_contract.py',
         'server/tests/test_release_0420_packaging_integrity.py',
         'server/nltk_resources.py', 'server/pc_copy_verification.py',
         'installer/prepare_nltk_data.py', 'installer/repair_installed_nltk_data.ps1',
         'server/tests/test_nltk_resource_packaging.py', 'server/tests/test_pc_copy_verification.py',
         'server/tests/test_android_local_audio_removal_contract.py',
         'app/src/main/java/com/firstsoundhelper/LocalAudioDeletionPolicy.kt',
         'app/src/test/java/com/firstsoundhelper/LocalAudioDeletionPolicyTest.kt',
         'app/src/test/java/com/firstsoundhelper/LocalSpeechRecordingRemovalTest.kt')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    validation = json.loads((ROOT / 'installer/output/BUILD_0.4.21_VALIDATION.json').read_text())
    stamp_path = ROOT / 'dist/HearliumParentPC/layer2_build_integrity.json'
    stamp = json.loads(stamp_path.read_text())
    assert validation['version'] == '0.4.21' and validation['bundleUnchangedDuringCompilation'] is True
    for name, expected in stamp['filesSha256'].items():
        assert digest(ROOT / name) == expected, name
    assert validation['executableSha256'] == digest(ROOT / 'dist/HearliumParentPC/HearliumParentPC.exe')
    assert validation['sha256'] == digest(ROOT / 'installer/output/HearliumSetup-0.4.21.exe')
    programs = {n: h for n, h in stamp['filesSha256'].items() if not n.startswith('dist/')}
    proof = dict(version='0.4.21', sourceOnly=True, checkedUtc=datetime.now(timezone.utc).isoformat(),
                 verifiedProgramFiles=programs, verifiedProgramFileCount=len(programs),
                 testedBuildStampSha256=digest(stamp_path), installerVerification=validation,
                 androidVersion='3.3.4/code10', androidSourceGuard='passed',
                 gradleVersion='8.9', remoteApkBuild='not run', installedDeviceAcceptance='pending')
    proof['nltkResources'] = json.loads((ROOT / 'models/nltk_data/resources_sha256.json').read_text())
    kotlin_proof = json.loads((ROOT / 'reports/0421_kotlin_policy_tests.json').read_text())
    assert kotlin_proof['passed'] > 0 and kotlin_proof['failures'] == 0
    for name, expected in kotlin_proof['filesSha256'].items():
        assert digest(ROOT / name) == expected, name
    proof['kotlinPolicyTests'] = kotlin_proof
    proof['androidCleanupProtocol'] = 'android-local-audio-removal-v1'
    proof['androidCleanupApproval'] = 'caregiver confirms after fresh PC stored-copy verification'
    (ROOT / 'SOURCE_RELEASE_0.4.21_VERIFICATION.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    manifest_path = ROOT / 'SOURCE_MANIFEST_SHA256.json'
    names = set(json.loads(manifest_path.read_text())) | set(ADDED)
    forbidden_dirs = {'.git', '.venv', '.installer_venv', 'models', 'reports', 'build', 'dist', '__pycache__'}
    forbidden_suffixes = {'.exe', '.dll', '.pyd', '.wav', '.apk', '.aab', '.pyc', '.log', '.bak', '.zip', '.keystore', '.jks'}
    for name in names:
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or set(p.parts) & forbidden_dirs or p.suffix.lower() in forbidden_suffixes:
            raise RuntimeError('Forbidden package entry: ' + name)
        if p.name.startswith('.env') and p.name != '.env.example':
            raise RuntimeError('Private environment file: ' + name)
        if (ROOT / p).is_symlink():
            raise RuntimeError('Symlink excluded: ' + name)
    manifest = {name: digest(ROOT / name) for name in sorted(names)}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    release = ROOT / 'release_0.4.21'
    stage = release / 'Hearlium_0.4.21_GitHub_Ready'
    if stage.exists():
        raise RuntimeError('Stage already exists; preserve it and select a new destination')
    stage.mkdir(parents=True)
    for name in sorted(names | {'SOURCE_MANIFEST_SHA256.json'}):
        destination = stage / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
        assert digest(destination) == digest(ROOT / name), name
    target = release / 'Hearlium_0.4.21_GitHub_Ready.zip'
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in sorted(stage.rglob('*')):
            if p.is_file():
                archive.write(p, p.relative_to(release).as_posix())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert len(archive.infolist()) == len(names) + 1
        for name, expected in manifest.items():
            assert hashlib.sha256(archive.read(stage.name + '/' + name)).hexdigest() == expected, name
    target.with_suffix('.zip.sha256').write_text(digest(target) + '  ' + target.name + '\n', encoding='ascii')
    print(json.dumps({'archive': str(target), 'sha256': digest(target),
                      'files': len(names) + 1, 'bytes': target.stat().st_size}, indent=2))


if __name__ == '__main__':
    main()
