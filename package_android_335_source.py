"""Package the Android-only hotfix with current hashes and actual local test proof."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
ADDED = (
    'app/src/main/java/com/firstsoundhelper/LocalAudioRemovalDialog.kt',
    'app/src/main/java/com/firstsoundhelper/AndroidBuildInfo.kt',
    'app/src/test/java/com/firstsoundhelper/LocalAudioRemovalDialogTest.kt',
    'app/src/test/java/com/firstsoundhelper/AndroidBuildInfoTest.kt',
    'server/tests/test_android_build_info_contract.py',
    'ANDROID_HOTFIX_3.3.5.md', 'ANDROID_3.3.5_VALIDATION.json',
    'package_android_335_source.py',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    suites = [ET.parse(p).getroot() for p in
              (WORKSPACE / 'build/android335/build/test-results/test').glob('TEST-*.xml')]
    assert suites and all(int(s.get('failures')) == 0 and int(s.get('errors')) == 0 for s in suites)
    count = sum(int(s.get('tests')) - int(s.get('skipped')) for s in suites)
    assert count == 18
    generated = (ROOT / 'app/build/generated/source/buildConfig/debug/com/firstsoundhelper/BuildConfig.java').read_text()
    assert 'VERSION_CODE = 11;' in generated and 'VERSION_NAME = "3.3.5";' in generated
    assert 'BUILD_GRADLE_VERSION = "8.9";' in generated and 'BUILD_AGP_VERSION = "8.7.3";' in generated
    pc = json.loads((ROOT / 'SOURCE_RELEASE_0.4.21_VERIFICATION.json').read_text())
    for name, expected in pc['verifiedProgramFiles'].items():
        assert digest(ROOT / name) == expected, 'Parent PC source changed: ' + name
    proof = {'androidVersion': '3.3.5/code11', 'parentPcVersion': '0.4.21',
             'checkedUtc': datetime.now(timezone.utc).isoformat(), 'jvmTestsPassed': count,
             'jvmSuites': {s.get('name'): int(s.get('tests')) for s in suites},
             'uiScope': 'Robolectric API 28; narrow portrait, font scale 2.0, large-text landscape',
             'pythonAndroidContractTestsPassed': 11, 'androidSourceGuard': 'passed',
             'actualGradleConfiguration': 'passed', 'actualBuildConfigGeneration': 'passed',
             'generatedGradleVersion': '8.9', 'generatedAgpVersion': '8.7.3',
             'parentPcProgramSourceHashesUnchanged': True,
             'apkCompilation': 'not run locally', 'physicalDeviceAcceptance': 'pending',
             'installed': False, 'remoteGithubWrite': False}
    (ROOT / 'ANDROID_3.3.5_VALIDATION.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    manifest_path = ROOT / 'SOURCE_MANIFEST_SHA256.json'
    names = set(json.loads(manifest_path.read_text())) | set(ADDED)
    forbidden = {'.git', '.gradle', 'build', 'models', 'reports', '.venv', '.installer_venv', '__pycache__'}
    for name in names:
        p = Path(name)
        assert not p.is_absolute() and '..' not in p.parts and not set(p.parts) & forbidden, name
        assert p.suffix.lower() not in {'.exe', '.dll', '.jar', '.apk', '.wav', '.pyc', '.zip', '.keystore', '.jks'}, name
    manifest = {n: digest(ROOT / n) for n in sorted(names)}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    target = WORKSPACE / 'Hearlium_Android_3.3.5_GitHub_Ready.zip'
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(names | {'SOURCE_MANIFEST_SHA256.json'}):
            archive.write(ROOT / name, name)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert 'app/build.gradle' in archive.namelist()
        for name, expected in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected, name
        gradle = archive.read('app/build.gradle').decode()
        assert re.search(r'(?m)^\s*versionCode\s+11\s*$', gradle)
    checksum = digest(target)
    target.with_suffix('.zip.sha256').write_text(checksum + '  ' + target.name + '\n', encoding='ascii')
    print(json.dumps({'archive': str(target), 'files': len(names) + 1,
                      'bytes': target.stat().st_size, 'sha256': checksum}, indent=2))


if __name__ == '__main__':
    main()
