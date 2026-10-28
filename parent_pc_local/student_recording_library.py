"""Read-only student recording indexing and audited display-name mapping.

A friendly name is a label for a stable speaker ID, never a reassignment of
recording identity. Recordings and their original metadata are not modified.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, date, timezone
from pathlib import Path

_PROFILE_LOCK = threading.RLock()
_UNASSIGNED_IDS = {'', 'anonymous', 'student-1', 'unknown', 'unassigned'}


def is_unassigned(speaker_id: object) -> bool:
    return str(speaker_id or '').strip().casefold() in _UNASSIGNED_IDS


def student_display_name(speaker_id: object, metadata: dict, profiles: dict) -> str:
    key = str(speaker_id or '').strip()
    # Android's explicit caregiver label belongs to one recording. A phone's
    # speaker ID can be shared by several children, so never update the
    # speaker-profile map or imply that a label verifies speaker identity.
    if (metadata.get('source') == 'android' and
            metadata.get('studentNameSource') == 'caregiver_on_android'):
        label = str(metadata.get('studentName') or '').strip()
        if label and len(label) <= 120 and not any(ord(ch) < 32 or ord(ch) == 127 for ch in label):
            return label + ' (phone label)'
    if is_unassigned(key):
        return 'Unassigned'
    entry = profiles.get(key, {})
    alias = entry.get('displayName', '') if isinstance(entry, dict) else ''
    return str(alias or metadata.get('studentName') or key).strip() or key


def load_profiles(path: Path) -> dict:
    with _PROFILE_LOCK:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, OSError, ValueError, UnicodeError):
            return {}


def assign_display_name(profile_file: Path, audit_file: Path, speaker_id: str, name: str) -> None:
    speaker_id, name = str(speaker_id).strip(), str(name).strip()
    if is_unassigned(speaker_id):
        raise ValueError('This recording has a shared or missing ID. Do not give it a student name without verified reassignment.')
    if not name or len(name) > 120 or any(ord(ch) < 32 for ch in name):
        raise ValueError('Enter a student name of 1 to 120 characters, without control characters.')
    with _PROFILE_LOCK:
        profiles = load_profiles(profile_file)
        old = profiles.get(speaker_id)
        old_name = old.get('displayName', '') if isinstance(old, dict) else ''
        if old_name == name:
            return
        profile_file.parent.mkdir(parents=True, exist_ok=True)
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        event_id = uuid.uuid4().hex
        when = datetime.now(timezone.utc).isoformat()

        def audit(event_type: str):
            entry = {'eventId': event_id, 'event': event_type, 'time': when,
                     'speakerId': speaker_id, 'oldDisplayName': old_name,
                     'newDisplayName': name}
            with audit_file.open('a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                f.flush()
                os.fsync(f.fileno())

        # Record intention before changing the mapping; the 'committed' entry
        # distinguishes successful updates from interrupted attempts.
        audit('change_requested')
        profiles[speaker_id] = {'displayName': name}
        tmp = profile_file.with_name(profile_file.name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            with tmp.open('x', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, profile_file)
        finally:
            tmp.unlink(missing_ok=True)
        audit('change_committed')


def parse_day(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('Dates must be YYYY-MM-DD (for example, 2026-10-23).') from exc


def get_recording_day(record: dict) -> date | None:
    stamp = str(record.get('created', '')).strip()
    try:
        return date.fromisoformat(stamp[:10])
    except ValueError:
        return None


def filter_and_sort(rows: list[dict], *, speaker_id: str = 'ALL',
                    search: str = '', date_from: str = '', date_to: str = '',
                    sort_by: str = 'Newest first') -> list[dict]:
    begin, end = parse_day(date_from), parse_day(date_to)
    if begin and end and begin > end:
        raise ValueError('The starting date must be on or before the ending date.')
    needle = search.strip().casefold()
    out = []
    for row in rows:
        sid = str(row.get('speakerId') or '').strip()
        if speaker_id == '__UNASSIGNED__':
            if not is_unassigned(sid):
                continue
        elif speaker_id != 'ALL' and sid != speaker_id:
            continue
        fields = ('displayName', 'speakerId', 'filename', 'word', 'title', 'suggestedTitle',
                  'customTitle', 'labelNotes', 'tags')
        if needle and not any(needle in str(row.get(f) or '').casefold() for f in fields):
            continue
        day = get_recording_day(row)
        if begin and (day is None or day < begin):
            continue
        if end and (day is None or day > end):
            continue
        out.append(row)

    if sort_by == 'Oldest first':
        return sorted(out, key=lambda r: (str(r.get('created', '')), str(r.get('filename', ''))))
    if sort_by == 'Student A–Z':
        return sorted(out, key=lambda r: (str(r.get('displayName', '')).casefold(), -float(r.get('mtime', 0)), str(r.get('filename', ''))))
    if sort_by == 'Student Z–A':
        return sorted(out, key=lambda r: (str(r.get('displayName', '')).casefold(), float(r.get('mtime', 0)), str(r.get('filename', ''))), reverse=True)
    if sort_by == 'Recording name A–Z':
        return sorted(out, key=lambda r: str(r.get('filename', '')).casefold())
    if sort_by == 'Recording name Z–A':
        return sorted(out, key=lambda r: str(r.get('filename', '')).casefold(), reverse=True)
    if sort_by == 'Recording title A–Z':
        return sorted(out, key=lambda r: (str(r.get('title', '')).casefold(), str(r.get('filename', ''))))
    if sort_by == 'Recording title Z–A':
        return sorted(out, key=lambda r: (str(r.get('title', '')).casefold(), str(r.get('filename', ''))), reverse=True)
    extra_sorts = {
        'Speaker ID A–Z': ('speakerId', False), 'Speaker ID Z–A': ('speakerId', True),
        'Review status A–Z': ('status', False), 'Review status Z–A': ('status', True),
        'Word / suggestion A–Z': ('word', False), 'Word / suggestion Z–A': ('word', True),
    }
    if sort_by in extra_sorts:
        field, descending = extra_sorts[sort_by]
        return sorted(out, key=lambda r: (str(r.get(field, '')).casefold(),
                                           str(r.get('filename', '')).casefold()), reverse=descending)
    # Recording time is the saved createdAt timestamp. WAV modification time
    # may change when audio is copied/imported and must not change the
    # historical chronological order of recordings.
    return sorted(out, key=lambda r: (str(r.get('created', '')), str(r.get('filename', ''))), reverse=True)
