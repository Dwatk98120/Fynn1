"""Synthetic frozen checks for corroborated legacy aliases; no real data writes."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tempfile
import wave


def _snapshot(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}


def run_check():
    try:
        from server.android_recording_storage import _reuse_reanalysis_original
    except ModuleNotFoundError:
        from android_recording_storage import _reuse_reanalysis_original

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\x00\x00' * 1600)
    raw = buffer.getvalue()
    digest = hashlib.sha256(raw).hexdigest()
    with tempfile.TemporaryDirectory(prefix='hearlium-legacy-alias-') as temporary:
        root = Path(temporary)
        recordings, results = root / 'recordings', root / 'results'
        recordings.mkdir()
        results.mkdir()
        historical = results / 'historical.json'
        historical.write_bytes(b'{"historical":true}')
        legacy = {'recordingId': 'gate-recording', 'speakerId': 'gate-speaker',
                  'recordingFile': '0_legacy.wav',
                  'analysisResult': {'recordingId': 'gate-recording', 'speakerId': 'gate-speaker',
                    'recordingStorage': {'saved': True, 'source': 'android', 'sha256': digest}}}
        receipt = {'recordingId': 'gate-recording', 'speakerId': 'gate-speaker',
                   'source': 'android', 'audioSha256': digest,
                   'audioBytes': len(raw), 'originalAudioImmutable': True}
        for name, metadata in (('0_legacy', legacy), ('a_android', receipt), ('z_android', receipt)):
            (recordings / (name + '.wav')).write_bytes(raw)
            (recordings / (name + '.json')).write_text(json.dumps(metadata), encoding='utf-8')
        before = _snapshot(root)
        reused = _reuse_reanalysis_original(recordings, results, raw, 'gate-recording',
                                            'gate-speaker', {'syntheticBuildCheck': True})
        if Path(reused['wav']).name != 'a_android.wav' or reused.get('source') != 'android':
            raise RuntimeError('Frozen legacy alias recovery did not select a verified receipt')
        note = reused.get('legacyAliasCorroboration') or {}
        if (note.get('version') != 'legacy-source-absent-alias-corroboration-v1'
                or note.get('aliasCount') != 1 or note.get('unknownProvenancePreserved') is not True
                or note.get('physicalCaptureSourceVerified') is not False):
            raise RuntimeError('Frozen legacy provenance annotation is missing')
        payload = json.loads(Path(reused['analysis']).read_text(encoding='utf-8'))
        if payload['recordingStorage'].get('legacyAliasCorroboration') != note:
            raise RuntimeError('Frozen result lost its legacy alias annotation')
        after = _snapshot(root)
        if any(after.get(path) != checksum for path, checksum in before.items()):
            raise RuntimeError('Frozen legacy recovery changed original data')
        added = set(after) - set(before)
        expected_export = Path(reused['analysis']).relative_to(root).as_posix()
        if added != {expected_export}:
            raise RuntimeError('Frozen legacy recovery created an unexpected file')
        metadata = json.loads((recordings / '0_legacy.json').read_text(encoding='utf-8'))
        if 'source' in metadata or 'audioSha256' in metadata:
            raise RuntimeError('Frozen legacy recovery rewrote missing provenance')

        # Exercise modern receipts too: their top-level hashes must never
        # hide contradictory identity or source in any same-ID copy.
        conflicting_receipts = [dict(receipt, source='parent_pc')]
        for field in ('source', 'recordingId', 'speakerId'):
            analysis = {'recordingId': 'gate-recording', 'speakerId': 'gate-speaker',
                        'recordingStorage': {'source': 'android', 'sha256': digest, 'saved': True}}
            if field == 'source':
                analysis['recordingStorage']['source'] = 'parent_pc'
            else:
                analysis[field] = 'conflicting-identity'
            conflicting_receipts.append(dict(receipt, analysisResult=analysis))
        receipt_path = recordings / 'z_android.json'
        original_receipt_bytes = receipt_path.read_bytes()
        for conflicting in conflicting_receipts:
            receipt_path.write_text(json.dumps(conflicting), encoding='utf-8')
            before_reject = _snapshot(root)
            try:
                _reuse_reanalysis_original(recordings, results, raw, 'gate-recording',
                                           'gate-speaker', {'syntheticBuildCheck': True})
            except ValueError as exc:
                if 'identity_conflict' not in str(exc):
                    raise RuntimeError('Frozen receipt conflict rejected for an unexpected reason') from exc
            else:
                raise RuntimeError('Frozen legacy guard accepted a conflicting modern receipt')
            if _snapshot(root) != before_reject:
                raise RuntimeError('Rejected frozen receipt conflict changed files')
            receipt_path.write_bytes(original_receipt_bytes)

        # A good canonical receipt must never hide damage in another same-ID WAV.
        (recordings / '0_legacy.wav').write_bytes(raw[:-2])
        before_reject = _snapshot(root)
        try:
            _reuse_reanalysis_original(recordings, results, raw, 'gate-recording',
                                       'gate-speaker', {'syntheticBuildCheck': True})
        except ValueError as exc:
            if str(exc) != 'reanalysis_original_integrity_conflict':
                raise RuntimeError('Frozen legacy guard rejected for an unexpected reason') from exc
        else:
            raise RuntimeError('Frozen legacy guard accepted a damaged same-ID alias')
        if _snapshot(root) != before_reject:
            raise RuntimeError('Rejected frozen legacy recovery changed files')
    return {'passed': True, 'legacyAliasHotfixVersion': '0.4.19',
            'canonicalSource': 'android', 'syntheticOriginalWavCount': 3,
            'unknownProvenancePreserved': True, 'tamperedAliasRejected': True,
            'receiptConflictsRejected': True}
