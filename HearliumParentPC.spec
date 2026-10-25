# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# The launcher dispatches --server / --record / --pair in the same frozen EXE.
datas = []
binaries = []
hiddenimports = []
for pkg in ['torch', 'transformers', 'tokenizers', 'numpy', 'sounddevice', 'soundfile',
            'requests', 'fastapi', 'uvicorn', 'h11', 'g2p_en', 'nltk', 'inflect', 'distance',
            'safetensors', 'huggingface_hub', 'multipart', 'faster_whisper', 'av', 'ctranslate2',
            'silero_vad']:
    try:
        d, b, h = collect_all(pkg)
        datas.extend(d)
        binaries.extend(b)
        hiddenimports.extend(h)
    except Exception as exc:
        raise RuntimeError('Required PyInstaller collection failed for %s: %s' % (pkg, exc))

# Bundle offline word-ASR model; the build must download/validate it first.
from pathlib import Path
model_dir = Path('models/faster-whisper-base.en')
if not (model_dir / 'model.bin').is_file():
    raise RuntimeError('Offline Faster-Whisper model missing: run installer\\prepare_whisper_model.py')
datas.append((str(model_dir), 'models/faster-whisper-base.en'))

# A newly installed Parent PC must not require a network connection to load
# the independent phoneme recognizer for its first recording.
phoneme_model_dir = Path('models/phoneme-wav2vec2')
if not (phoneme_model_dir / 'config.json').is_file() or not any(
    (phoneme_model_dir / name).is_file() for name in ('model.safetensors', 'pytorch_model.bin')
):
    raise RuntimeError('Offline phoneme model missing: run installer\\prepare_phoneme_model.py')
datas.append((str(phoneme_model_dir), 'models/phoneme-wav2vec2'))
# Keep licensing terms with the distributed offline Silero model.
datas.append(('THIRD_PARTY_NOTICES_SILERO_VAD.md', '.'))

# Include any non-Python model/data assets bundled with this project.
datas.extend(collect_data_files('certifi'))
a = Analysis(
    ['parent_pc_local/hearlium_launcher.py'],
    pathex=['parent_pc_local', 'server', '.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports + ['main', 'direct_recording', 'pair_phone',
        'hearlium_parent_pc_gui', 'phase3_learning_gui', 'layer_health', 'temporal_prosody', 'candidate_word_engine',
        'learning_engine', 'learning_store', 'analysis_engine', 'phoneme_analysis',
        'phoneme_substitution', 'recording_quality', 'silero_activity',
        'server.silero_activity', 'reference_audio', 'reference_audio_gui',
        'learning_contracts', 'repair_pipeline', 'segment_interpretation', 'number_review',
        'word_asr', 'speech_activity_review', 'server.speech_activity_review',
        'phoneme_timing_review', 'server.phoneme_timing_review',
        'speech_activity_candidate_review', 'server.speech_activity_candidate_review',
        'utterance_prosody_review', 'server.utterance_prosody_review',
        'word_asr_activity_review', 'server.word_asr_activity_review',
        'speech_window_quality_review', 'server.speech_window_quality_review',
        'recognizer_disagreement_review', 'server.recognizer_disagreement_review',
        'analysis_jobs', 'analysis_client', 'caregiver_review_guidance', 'student_recording_library',
        'recording_title_store', 'api_diagnostics', 'bootstrap_server',
        'android_recording_storage', 'server.android_recording_storage'])),
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='HearliumParentPC',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False,
               name='HearliumParentPC')
