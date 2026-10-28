"""Create a browser-uploadable Android-only source ZIP (standard library only)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent


def package(output):
    subprocess.run([sys.executable, '-B', str(ROOT / 'android_no_live_verify.py'), '--source'], check=True)
    gradle = (ROOT / 'app/build.gradle').read_text(encoding='utf-8')
    version = re.search(r"versionName\s+['\"]([^'\"]+)['\"]", gradle).group(1)
    code = re.search(r'versionCode\s+(\d+)', gradle).group(1)
    required = ['build.gradle', 'settings.gradle', 'gradle.properties', 'gradlew',
                'gradlew.bat', 'android_no_live_verify.py', 'AGENTS.md',
                'package_android_small.py', 'ANDROID_SMALL_UPLOAD.md',
                'gradle/wrapper/gradle-wrapper.properties',
                '.github/workflows/build-apk.yml',
                '.github/workflows/build-apk-recording-fix.yml']
    names = set(required)
    names.add('app/build.gradle')
    for path in (ROOT / 'app/src').rglob('*'):
        if path.is_file():
            relative = path.relative_to(ROOT)
            if any(part.startswith('.') or part in {'build', '__pycache__'} for part in relative.parts):
                raise ValueError('Unexpected source path: ' + str(relative))
            if path.suffix.lower() not in {'.kt', '.java', '.xml'}:
                raise ValueError('Review new Android asset before packaging: ' + str(relative))
            names.add(relative.as_posix())
    data = {name: (ROOT / name).read_bytes() for name in sorted(names)}
    for name in ('LICENSE_NOTICE.md', '.gitignore'):
        if (ROOT / name).is_file():
            data[name] = (ROOT / name).read_bytes()
    data['ANDROID_UPLOAD_MANIFEST_SHA256.json'] = (json.dumps(
        {name: hashlib.sha256(blob).hexdigest() for name, blob in sorted(data.items())},
        indent=2) + '\n').encode()
    if len(data) > 100:
        raise ValueError(f'{len(data)} files exceeds browser upload limit; use Git/Desktop or prepare batches. No ZIP created.')
    output.mkdir(parents=True, exist_ok=True)
    target = output / f'Hearlium_Android_{version}_code{code}_SMALL_Upload.zip'
    # Exclusive creation preserves earlier artifacts; choose a new output folder to repeat.
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, blob in sorted(data.items()):
            archive.writestr(name, blob)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(data)
        for name, blob in data.items():
            assert archive.read(name) == blob, name
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(checksum + '  ' + target.name + '\n', encoding='ascii')
    print(json.dumps({'zip': str(target), 'files': len(data), 'sha256': checksum,
                      'apkCompiled': False, 'deviceAcceptance': 'pending'}, indent=2))
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    package(args.output_dir.resolve())
