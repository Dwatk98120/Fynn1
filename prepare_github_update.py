"""Prepare a source-only, locally audited update; never publish anything."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / 'github_update_staging' / 'Hearlium_0.4.15_GitHub_Update'
SKIP_DIRS = {'.git', '.github_update_staging', 'github_update_staging', '.installer_venv',
    '.pytest_cache', '__pycache__', 'build', 'dist', 'bin', 'obj', 'models',
    '.gradle', '.idea', '.venv', 'venv', 'node_modules', 'output', 'prereqs',
    'recordings', 'student_data', 'student_profiles', 'reports', 'data', '.aws', '.codex', '.agents'}
SAFE_EXT = {'.py', '.md', '.txt', '.kt', '.java', '.xml', '.gradle', '.bat', '.ps1',
    '.properties', '.yml', '.yaml', '.json', '.cs', '.csproj', '.iss', '.spec'}
SPECIAL = {'.gitignore', 'gradlew', '.env.example', 'local.properties.example'}
OMIT = {'prepare_github_update.py', 'test_results_0.4.10.txt'}
PATTERNS = {
    'private_key': r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'github_token': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'aws_access_key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'openai_key': r'\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b',
    'slack_token': r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
    'credential_url': r'https?://[^\s/:@]+:[^\s/@]+@',
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def scan(text):
    return [name for name, pattern in PATTERNS.items() if re.search(pattern, text)]

def write(name, content):
    (STAGE / name).write_text(content, encoding='utf-8')

def main():
    if STAGE.exists():
        raise SystemExit('Staging destination exists; refusing to overwrite.')
    candidates, exclusions, findings = [], [], []
    for folder, dirs, files in os.walk(ROOT):
        for name in list(dirs):
            if name.lower() in SKIP_DIRS:
                exclusions.append(str((Path(folder) / name).relative_to(ROOT)).replace('\\', '/') + '/')
                dirs.remove(name)
        for name in files:
            path = Path(folder) / name
            rel = path.relative_to(ROOT).as_posix()
            if (name in OMIT or (name.startswith('.env') and name != '.env.example')
                or name == 'local.properties' or (path.suffix.lower() not in SAFE_EXT and name not in SPECIAL)):
                exclusions.append(rel)
                continue
            if path.is_symlink() or path.stat().st_size > 5_000_000:
                raise SystemExit('Unexpected link or oversized candidate: ' + rel)
            text = path.read_text(encoding='utf-8-sig')
            hits = scan(text)
            if hits:
                findings.append({'file': rel, 'categories': hits})
            candidates.append((path, rel))
    if findings:
        print(json.dumps(findings, indent=2))
        raise SystemExit('Sensitive pattern matches require review before copying.')
    STAGE.mkdir(parents=True)
    for path, rel in candidates:
        target = STAGE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    baseline = []
    for backup in ROOT.rglob('*.bak'):
        if any(part.lower() in SKIP_DIRS for part in backup.relative_to(ROOT).parts):
            continue
        rel = backup.relative_to(ROOT).as_posix()
        original = rel.split('.20261027_')[0]
        current = ROOT / original
        if current.is_file():
            baseline.append({'file': original, 'baselineFile': rel,
                'baselineSha256': digest(backup), 'currentSha256': digest(current),
                'changed': digest(backup) != digest(current)})
    write('BASELINE_COMPARISONS.json', json.dumps(baseline, indent=2) + '\n')
    lines = ['# Changed files and available baseline', '',
        'No complete Git baseline or branch checkout was available. This is not a complete branch diff, and no deletions are inferred.', '',
        '## Hash-verified comparisons', '',
        '| Current file | Available backup | Result |', '|---|---|---|']
    for item in baseline:
        lines.append('| ' + item['file'] + ' | ' + item['baselineFile'] + ' | ' + ('Changed' if item['changed'] else 'Identical') + ' |')
    lines += ['', 'Backup names identify their provenance: most are pre-0.4.14 / 0.4.13 snapshots; only the explicitly named 0.4.14 test backup is an identified 0.4.14 snapshot. Hashes are in BASELINE_COMPARISONS.json. Backups themselves are excluded.', '',
        '## 0.4.15 changes known from this session', '',
        '- Modified: parent_pc_local/direct_recording.py; parent_pc_local/hearlium_parent_pc_gui.py; installer/Hearlium.iss; installer/verify_layer2_build.py; server/tests/test_build_0412_reanalysis_route.py; server/tests/test_phase3_parent_pc_source_review_hotfix.py; BUILD_VERSION.txt; BACKLOG_REVIEW_20261027.md.',
        '- Added: parent_pc_local/reanalysis_integrity.py; server/tests/test_build_0415_integrity.py; BUILD_0.4.15_README.txt.',
        '- Package-only updates: ROOT_UPLOAD_CHECK.txt replaces obsolete Main upload instructions; README.md gains current update guidance; .gitignore gains generated/private build exclusions.',
        '- Package-only additions: this changed-files list, baseline comparisons, GitHub update instructions, test/validation records, safety review and source manifest.', '',
        'Earlier application files are carried forward in full. Their differences from the remote branch are unknown until reviewed against that branch.']
    write('CHANGED_FILES_0.4.15.md', '\n'.join(lines) + '\n')
    write('ROOT_UPLOAD_CHECK.txt', 'HEARLIUM 0.4.15 - BRANCH 2 SOURCE UPDATE\n\nTarget branch: hearlium-parent-pc-integration\nRead GITHUB_UPDATE_INSTRUCTIONS.md before copying files.\nCopy folder contents into the repository root, not as a nested folder.\nLeave Main untouched. Do not follow historical Main upload instructions.\nNo models, binaries, installed data or Git history are included.\n')
    readme = STAGE / 'README.md'
    readme.write_text('# Hearlium 0.4.15 Branch 2 update\n\nTarget: `hearlium-parent-pc-integration`. Start with [GITHUB_UPDATE_INSTRUCTIONS.md](GITHUB_UPDATE_INSTRUCTIONS.md), [BUILD_0.4.15_README.txt](BUILD_0.4.15_README.txt), and [BACKLOG_REVIEW_20261027.md](BACKLOG_REVIEW_20261027.md).\n\nOlder documentation below is historical and may describe obsolete architecture, versions, workflows or Main deployment instructions. The update instructions above take precedence for this package. Parent PC is 0.4.15; Android remains 3.3.3/code9.\n\n---\n\n' + readme.read_text(encoding='utf-8'), encoding='utf-8')
    with (STAGE / '.gitignore').open('a', encoding='utf-8') as stream:
        stream.write('\n# Generated/private build material excluded from this update\n.installer_venv/\n.pytest_cache/\n**/bin/\n**/obj/\ninstaller/output/\ninstaller/prereqs/\nmodels/\n*.exe\n*.dll\n*.log\n*.bak\n*.pfx\n*.pem\n*.key\n')
    write('GITHUB_UPDATE_INSTRUCTIONS.md', '''# Update Branch 2 with Hearlium 0.4.15

Target branch: `hearlium-parent-pc-integration`. Leave Main untouched.
This is a source-only handoff. No push, merge or remote change was performed.

1. Back up your existing Branch 2 working files separately. Keep recordings,
   learning data and credentials outside the checkout and this update folder.
2. In your existing repository, inspect `git status`. Preserve uncommitted work
   before switching branches. Run `git switch hearlium-parent-pc-integration`
   and confirm `git branch --show-current` prints that exact branch. If it is
   unavailable, stop and resolve the branch setup before copying anything.
3. Review CHANGED_FILES_0.4.15.md. The available baseline is partial; compare
   this complete source snapshot with your Branch 2 checkout before replacing
   files. Preserve newer branch-specific changes. No deletion list is provided.
4. Copy this folder's CONTENTS into the Branch 2 repository root, including
   `.github` and `.gitignore`. Do not nest the whole folder in the repository.
   Do not mirror-delete files or replace `.git`. Do not copy installed data.
5. Review `git status`, `git diff --stat` and `git diff`. Check for unexpected
   files, private data or conflicts. Historical notes may mention Main; do not
   follow those deployment commands for this update.
6. Set up a separate Python 3.12 build/test environment using the dependency
   setup in BUILD_HEARLIUM_INSTALLER.bat. Run `python -m pytest -q server/tests`
   and `python android_no_live_verify.py --source`. Compare actual results
   with TEST_RESULTS_0.4.15.md. Inspect failures instead of assuming old results
   apply to your environment.
7. For a fresh Windows installer, run BUILD_HEARLIUM_INSTALLER.bat from a
   short build path. It downloads prerequisites/models, rebuilds the Bluetooth
   helper, runs build gates and creates installer/output/HearliumSetup.exe.
   Models, prerequisite binaries and virtual environments are intentionally
   absent here. COMPILE_INSTALLER_ONLY.bat cannot build from this source-only
   package until a matching verified frozen build exists.
8. Android remains 3.3.3/code9. Wrapper scripts/properties are included but
   gradle-wrapper.jar is absent. Current workflows bootstrap Gradle 8.9 and
   regenerate the wrapper. build-apk.yml is manual; build-apk-recording-fix.yml
   targets Branch 2 pushes as well as manual dispatch. Remote run success and
   artifact availability have not been verified by this handoff.
9. Complete the installed-device checks in TEST_RESULTS_0.4.15.md before
   treating the update as validated on your devices.
10. If you later choose to commit, stage only reviewed source/docs on Branch 2
    and review the staged diff. Publishing is a separate user action. This
    handoff does not push, open a PR, merge, or update Main.

Safe examples `.env.example` and `local.properties.example` are included.
Do not commit real `.env`, local.properties, keys, recordings or model caches.
LICENSE_NOTICE.md still requires a project license choice before public release.
''')
    write('SENSITIVE_DATA_REVIEW.md', '''# Source handoff safety review

Candidate files were inspected before copying. Only UTF-8 source/configuration,
documentation, workflows and explicitly safe example files were eligible.
No binary assets were needed by the available source tree.

Excluded: build/dist, virtual environments, caches, .git/history, .aws/.codex/
.agents, downloaded models, installer output/prerequisites, .NET bin/obj,
recordings/student-data directories, .env except .env.example, local.properties,
binary extensions, backup files and private logs. Historical raw test output
was omitted; a fresh sanitized test transcript is provided instead.

Credential scanning checks private-key headers, common GitHub/AWS/OpenAI/Slack
token formats and credential-bearing URLs. A separate assignment/email/IP
review is recorded in SAFETY_SCAN_SUMMARY.json. Example/synthetic test data and
source strings referring to data fields are not actual installed student data.
No installed user-data directories were imported. This is a local source scan,
not an audit of remote Git history, remote settings or every possible secret format.
''')
    write('EXCLUDED_PATHS.json', json.dumps(sorted(exclusions), indent=2) + '\n')
    print(json.dumps({'stage': str(STAGE), 'copiedFiles': len(candidates), 'excludedEntries': len(exclusions), 'credentialPatternFindings': findings}))

if __name__ == '__main__':
    main()
