"""Read-only WAV snapshots and separate, uniquely named integrity reports."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def snapshot(folder):
    files = {}
    for path in sorted(Path(folder).glob('*.wav')):
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        files[path.name] = digest.hexdigest()
    return files


def save_report(folder, before, after, recording, request_succeeded):
    added = sorted(after.keys() - before.keys())
    missing = sorted(before.keys() - after.keys())
    changed = sorted(name for name in before.keys() & after.keys()
                     if before[name] != after[name])
    passed = not (added or missing or changed)
    report = {
        'build': '0.4.21', 'checkedUtc': datetime.now(timezone.utc).isoformat(),
        'recordingFile': Path(recording).name,
        'requestSucceeded': request_succeeded,
        'wavIntegrityPassed': passed,
        'beforeSha256': before, 'afterSha256': after,
        'addedWavs': added, 'missingWavs': missing, 'changedWavs': changed,
        'scope': 'Top-level WAV files in the selected recording folder; does not verify analysis accuracy, metadata or learning.',
    }
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / ('reanalysis_integrity_' + uuid.uuid4().hex + '.json')
    with path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
    return path, passed
