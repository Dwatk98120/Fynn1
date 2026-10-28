"""Isolated synthetic Android retry storage check. No phone or student data used."""
import hashlib
import io
import json
import os
import tempfile
import wave
from pathlib import Path
from unittest.mock import patch


def run_check():
    try:
        from server import android_recording_storage as storage
    except ImportError:
        import android_recording_storage as storage
    checks = {}
    def require(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise RuntimeError('Upload retry storage check failed: ' + name)
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        wav.writeframes(b'\x01\x00' * 3200)
    raw = buffer.getvalue()
    with tempfile.TemporaryDirectory(prefix='hearlium_retry_check_') as directory:
        root = Path(directory)
        with patch.dict(os.environ, {'LOCALAPPDATA': str(root), 'FSH_RECORDINGS_DIR': str(root / 'recordings')}):
            first = storage.store_android_recording(raw, 'synthetic-retry', 'synthetic-speaker', 'a', {}, student_name='Synthetic')
            protected = {key: Path(first[key]).read_bytes() for key in ('wav', 'metadata', 'analysis')}
            second = storage.store_android_recording(raw, 'synthetic-retry', 'synthetic-speaker', 'b', {}, student_name='Synthetic')
            require('same_original_reused', second['wav'] == first['wav'] and second.get('reused') is True)
            require('separate_analysis_result', second['analysis'] != first['analysis'])
            for label, changed_raw, speaker, source, name in (
                ('audio', raw + b'x', 'synthetic-speaker', 'android', 'Synthetic'),
                ('speaker', raw, 'different', 'android', 'Synthetic'),
                ('source', raw, 'synthetic-speaker', 'parent_pc', ''),
                ('name', raw, 'synthetic-speaker', 'android', 'Different')):
                rejected = False
                try:
                    storage.store_android_recording(changed_raw, 'synthetic-retry', speaker, 'c', {}, source=source, student_name=name)
                except ValueError:
                    rejected = True
                require(label + '_conflict_rejected', rejected)
            require('one_original_wav', len(list((root / 'recordings').glob('*.wav'))) == 1)
            require('all_original_files_unchanged', all(Path(first[k]).read_bytes() == v for k, v in protected.items()))
            require('original_hash_matches', hashlib.sha256(Path(first['wav']).read_bytes()).hexdigest() == hashlib.sha256(raw).hexdigest())
            # Exercise the release repair inside the frozen executable as well.
            pc = storage.store_android_recording(raw, 'legacy-pc', 'synthetic-speaker', 'a', {}, source='parent_pc')
            capture = root / 'recordings' / 'legacy_capture.json'
            capture.with_suffix('.wav').write_bytes(raw)
            legacy = {'source': 'parent_pc', 'speakerId': 'synthetic-speaker', 'recordingId': 'legacy-pc',
                      'analysisResult': {'speakerId': 'synthetic-speaker', 'recordingId': 'legacy-pc',
                                         'recordingStorage': {'saved': True, 'source': 'parent_pc', 'sha256': pc['sha256']}}}
            capture.write_text(json.dumps(legacy), encoding='utf-8')
            originals = {p: p.read_bytes() for p in (root / 'recordings').iterdir()}
            recovered = storage.store_android_recording(raw, 'legacy-pc', 'synthetic-speaker', 'b', {}, source='parent_pc', reanalysis=True)
            require('legacy_pc_reanalysis_reused', recovered.get('reused') is True)
            require('legacy_pc_originals_preserved', all(p.read_bytes() == data for p, data in originals.items())
                    and set(originals) == set((root / 'recordings').iterdir()))
            for label, change in (
                    ('legacy_recorded_hash', lambda: capture.write_text(json.dumps(dict(legacy, audioSha256='0' * 64)), encoding='utf-8')),
                    ('legacy_corrupt_wav', lambda: capture.with_suffix('.wav').write_bytes(b'corrupted'))):
                change()
                rejected = False
                try:
                    storage.store_android_recording(raw, 'legacy-pc', 'synthetic-speaker', 'c', {}, source='parent_pc', reanalysis=True)
                except ValueError:
                    rejected = True
                require(label + '_rejected', rejected)
                for path, data in originals.items():
                    path.write_bytes(data)
    return {'build': '0.4.17', 'passed': True, 'checks': checks,
            'scope': 'Synthetic local storage only; actual Android/network/installed-device tests remain pending.'}
