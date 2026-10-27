import hashlib
import json
from pathlib import Path
import re
from prepare_github_update import PATTERNS, SKIP_DIRS

root = Path(__file__).resolve().parent / 'github_update_staging' / 'Hearlium_0.4.15_GitHub_Update'
files = sorted(p for p in root.rglob('*') if p.is_file())
findings = []
addresses = set()
for path in files:
    rel = path.relative_to(root)
    if path.is_symlink() or any(part.lower() in SKIP_DIRS for part in rel.parts):
        raise SystemExit('Forbidden path: ' + rel.as_posix())
    if path.suffix.lower() in {'.exe', '.dll', '.wav', '.mp3', '.m4a', '.apk', '.aab', '.bin', '.bak', '.log', '.pyc', '.pfx', '.pem', '.key', '.jks', '.keystore'}:
        raise SystemExit('Forbidden file: ' + rel.as_posix())
    if path.name.startswith('.env') and path.name != '.env.example':
        raise SystemExit('Forbidden environment file')
    text = path.read_text(encoding='utf-8-sig')
    for category, pattern in PATTERNS.items():
        if re.search(pattern, text):
            findings.append({'file': rel.as_posix(), 'category': category})
    if re.search(r'(?i)(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*[^\s,}]+', text):
        findings.append({'file': rel.as_posix(), 'category': 'credential_assignment'})
    if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text):
        findings.append({'file': rel.as_posix(), 'category': 'email'})
    addresses.update(re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text))
if findings:
    print(json.dumps(findings, indent=2))
    raise SystemExit('Unreviewed safety findings')
summary = {
    'date': '2026-10-27', 'credentialPatternFindings': [],
    'credentialAssignmentFindings': [], 'emailFindings': [],
    'binaryOrForbiddenPathFindings': [],
    'reviewedAddressValues': sorted(addresses),
    'addressReview': 'Loopback, wildcard bind, Android emulator, public connectivity probe and documented/synthetic LAN examples; no installed connection configuration imported.',
    'safeConfigurationExamples': ['.env.example', 'local.properties.example'],
    'limitations': 'Pattern scan and source-only selection; not proof against every secret format or a remote history audit.',
}
(root / 'SAFETY_SCAN_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
manifest = {}
for path in sorted(root.rglob('*')):
    if path.is_file() and path.name != 'SOURCE_MANIFEST_SHA256.json':
        manifest[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
(root / 'SOURCE_MANIFEST_SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'filesIncludingManifest': len(manifest) + 1,
                  'bytes': sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),
                  'safetyFindings': 0, 'manifestEntries': len(manifest)}))
