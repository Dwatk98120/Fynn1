"""Opt-in alignment reports; never edit recordings, metadata or learning."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid


def save_alignment_report(wav_path, reference_text, destination, *, human_confirmed=False):
    if human_confirmed is not True:
        raise ValueError('Explicit human confirmation of the reference text is required')
    from reference_phoneme_alignment import align_reference_bytes
    wav_path, destination = Path(wav_path), Path(destination)
    if (destination.suffix.lower() != '.json'
            or destination.resolve() in (wav_path.resolve(), wav_path.with_suffix('.json').resolve())):
        raise ValueError('Alignment output must be a separate JSON file')
    if destination.exists():
        raise FileExistsError('An alignment report already exists at this path')
    raw = wav_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    report = align_reference_bytes(raw, reference_text, human_confirmed=human_confirmed)
    if hashlib.sha256(wav_path.read_bytes()).hexdigest() != digest:
        raise RuntimeError('Original audio changed during alignment; report not saved')
    report['originalWav'] = str(wav_path.resolve())
    report['originalSha256VerifiedAfterAlignment'] = digest
    # Validate serialization before creating any destination, so malformed
    # native/library results cannot leave a partial report that looks usable.
    serialized = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as stream:
        stream.write(serialized)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wav')
    parser.add_argument('--reference', required=True)
    parser.add_argument('--confirmed', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        save_alignment_report(args.wav, args.reference, args.output, human_confirmed=args.confirmed)
    except Exception as exc:
        # Windowed executables need a machine-readable error, not a modal crash.
        error = Path(args.output).with_suffix('.error.json')
        detail = f'{type(exc).__name__}: {exc}'
        try:
            error.parent.mkdir(parents=True, exist_ok=True)
            # Preserve any earlier failure report, just as successful reports
            # are immutable. The GUI supplies a fresh UUID destination.
            if error.exists():
                error = error.with_name(error.stem + '_' + uuid.uuid4().hex + '.json')
            with error.open('x', encoding='utf-8') as stream:
                json.dump({'passed': False, 'error': detail}, stream, ensure_ascii=False)
        except OSError:
            # An unavailable output directory must not replace the meaningful
            # alignment error with a second unhandled exception.
            pass
        if sys.stderr is not None:
            print('Alignment unavailable: ' + detail, file=sys.stderr)
        return 1
    return 0
