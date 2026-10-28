"""Frozen 0.4.18 checks using synthetic data and bundled model assets only."""
def run_check():
    import io
    import tempfile
    import wave
    from pathlib import Path
    import torch
    from server.ctc_segmentation import segment_ctc_phonemes, phoneme_confidences, propose_boundary_alternatives
    from server.review_vocabulary import COMMON_SENTENCE_WORDS
    from server.reference_phoneme_alignment import _create_decoder, normalize_reference_text
    from capture_identity import capture_identity
    if 'want' not in COMMON_SENTENCE_WORDS:
        raise RuntimeError('Frozen candidate dictionary is missing want')
    logits = torch.full((1, 15, 5), -4.0)
    ids = [1, 1] + [0] * 9 + [2, 2, 3, 3]
    for frame, token in enumerate(ids):
        logits[0, frame, token] = 1.0 if token == 1 else 8.0
    segments = segment_ctc_phonemes(logits, .3, {0:'[PAD]', 1:'w', 2:'n', 3:'t', 4:'|'},
                                    0, set(), '|', seconds_per_frame=.02)
    if len(segments) != 2 or segments[0]['confidence'] >= segments[1]['confidence']:
        raise RuntimeError('Frozen nonblank phoneme confidence is unavailable')
    if phoneme_confidences(segments[1]) != segments[1]['phonemeConfidences']:
        raise RuntimeError('Frozen token confidence mapping failed')
    if not propose_boundary_alternatives(segments):
        raise RuntimeError('Frozen boundary alternatives are missing')
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\x00\x00' * 1600)
    with tempfile.TemporaryDirectory(prefix='hearlium-capture-') as folder:
        path = Path(folder) / 'synthetic_capture.wav'
        path.write_bytes(buffer.getvalue())
        identity = capture_identity(path)
        if identity['recordingId'] != path.stem or identity['audioBytes'] != len(buffer.getvalue()):
            raise RuntimeError('Frozen first-analysis capture identity failed')
    decoder, provenance = _create_decoder()
    if not decoder.lookup_word('want') or not decoder.lookup_word('cookies'):
        raise RuntimeError('Bundled alignment dictionary incomplete')
    if normalize_reference_text('I want twenty-three cookies.') != 'i want twenty three cookies':
        raise RuntimeError('Reference normalization changed word order')
    return {'passed': True, 'phonemeHotfixVersion': '0.4.18',
            'engineVersion': provenance['engineVersion'], 'modelDirectory': provenance['modelDirectory']}
