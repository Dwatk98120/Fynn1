"""Source-only 0.4.16 handoff, excluding private/generated material."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile
from prepare_github_update import SAFE_EXT, SPECIAL, SKIP_DIRS, scan

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'release_0.4.16'
PACKAGE = OUT / 'Hearlium_0.4.16_GitHub_Update'
BASE = ROOT / 'github_update_staging' / 'Hearlium_0.4.15_GitHub_Update'
SKIP = SKIP_DIRS | {'release_0.4.16'}
OMIT = {'prepare_github_update.py', 'finalize_github_update.py',
        'package_0416_source.py', 'test_results_0.4.10.txt'}


def main():
    if PACKAGE.exists():
        raise RuntimeError('Refusing to overwrite an existing source package')
    candidates = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP]
        for name in files:
            path = Path(folder) / name
            if name in OMIT or name == 'local.properties' or (name.startswith('.env') and name != '.env.example'):
                continue
            if path.suffix.lower() not in SAFE_EXT and name not in SPECIAL:
                continue
            if path.is_symlink() or path.stat().st_size > 5_000_000:
                raise RuntimeError('Unexpected candidate: ' + str(path.relative_to(ROOT)))
            text = path.read_text(encoding='utf-8-sig')
            if scan(text):
                raise RuntimeError('Credential pattern requires review: ' + str(path.relative_to(ROOT)))
            candidates.append((path, path.relative_to(ROOT)))
    PACKAGE.mkdir(parents=True)
    changes = []
    for path, rel in candidates:
        target = PACKAGE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        old = BASE / rel
        if not old.exists():
            changes.append('Added: ' + rel.as_posix())
        elif old.read_bytes() != path.read_bytes():
            changes.append('Changed: ' + rel.as_posix())
    (PACKAGE / 'CHANGED_FILES_0.4.16.txt').write_text(
        'Baseline: preserved source-only 0.4.15 handoff in this workspace.\n'
        'Compared by file bytes; this is not a diff against the remote branch.\n'
        'Baseline package-only README/.gitignore differences are expected.\n'
        'No remote deletions are inferred.\n\n' + '\n'.join(changes) + '\n', encoding='utf-8')
    instructions = (BASE / 'GITHUB_UPDATE_INSTRUCTIONS.md').read_text(encoding='utf-8')
    instructions = instructions.replace('0.4.15', '0.4.16').replace('CHANGED_FILES_0.4.16.md', 'CHANGED_FILES_0.4.16.txt')
    instructions = instructions.replace('The available baseline is partial;', 'The baseline is the preserved local 0.4.15 source handoff;')
    (PACKAGE / 'GITHUB_UPDATE_INSTRUCTIONS.md').write_text(instructions, encoding='utf-8')
    (PACKAGE / 'ROOT_UPLOAD_CHECK.txt').write_text('HEARLIUM 0.4.16 BRANCH 2 UPDATE\nTarget: hearlium-parent-pc-integration. Leave Main untouched.\nRead GITHUB_UPDATE_INSTRUCTIONS.md before copying source.\n', encoding='utf-8')
    readme = PACKAGE / 'README.md'
    readme.write_text('# Hearlium 0.4.16 Branch 2\n\nStart with GITHUB_UPDATE_INSTRUCTIONS.md and BUILD_0.4.16_README.txt. Historical notes below may describe obsolete Main workflows; do not use those for this handoff.\n\n' + readme.read_text(encoding='utf-8'), encoding='utf-8')
    with (PACKAGE / '.gitignore').open('a', encoding='utf-8') as stream:
        stream.write('\n.installer_venv/\n.pytest_cache/\n**/bin/\n**/obj/\ninstaller/output/\ninstaller/prereqs/\nmodels/\nrelease_*/\ngithub_update_staging/\n*.exe\n*.dll\n*.log\n*.bak\n')
    (PACKAGE / 'TEST_RESULTS_0.4.16.md').write_text('''# Actual 0.4.16 validation

2026-10-27. Full server suite: 347 passed, 3 skipped in 7.25s; exit 0.
Android source safeguard verification: PASS. pip check: no broken requirements.
Silero offline model inference: PASS.
The three skips require optional private adult references, intentionally excluded.

Read-only replay of four private adult recordings through current candidate,
prosody and diagnostic code used 49/18/20/17 full energy peaks. Original WAV,
metadata and word-recognizer outputs were verified unchanged. Candidate coverage
improves but ranking errors remain. This was not fresh model inference, clinical
validation, a learning approval or installed-device acceptance.

Frozen and installer validation results, once completed, are recorded in the
separate BUILD_0.4.16_VALIDATION.json beside the downloadable installer.

PENDING: installed Windows reanalysis/integrity acceptance, actual phone/network
retry/conflict tests, model inference in the installed build, compound-reference
UI checks, and controlled feedback/learning holdouts for layers 9-13.
The new synthetic upload-storage check is not a substitute for these device tests.
''', encoding='utf-8')
    (PACKAGE / 'SENSITIVE_DATA_REVIEW.md').write_text('''# Source-only handoff review

UTF-8 source/config/docs/workflows and safe examples were scanned before copying.
Excluded: private reports/audio/JSON, logs, environment secrets, .git/history,
virtual environments, caches, generated .NET outputs, build/dist, downloaded
models, prerequisite executables and installers. Credential-pattern scan found
no private-key headers or common GitHub/AWS/OpenAI/Slack tokens/credential URLs.
Safe .env.example/local.properties.example remain examples only. This local
pattern review is not an audit of remote history or every possible secret type.
''', encoding='utf-8')
    manifest = {p.relative_to(PACKAGE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(PACKAGE.rglob('*')) if p.is_file()}
    (PACKAGE / 'SOURCE_MANIFEST_SHA256.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    archive = OUT / 'Hearlium_0.4.16_GitHub_Update.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(PACKAGE.rglob('*')):
            if path.is_file():
                bundle.write(path, path.relative_to(OUT))
    print(json.dumps({'files': len(manifest) + 1, 'changedOrAddedAgainstLocal0415': len(changes),
                      'zip': str(archive), 'bytes': archive.stat().st_size}))


if __name__ == '__main__':
    main()
