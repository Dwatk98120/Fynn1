# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# The launcher dispatches --server / --record / --pair in the same frozen EXE.
datas = []
binaries = []
hiddenimports = []
for pkg in ['torch', 'transformers', 'tokenizers', 'numpy', 'sounddevice', 'soundfile',
            'requests', 'fastapi', 'uvicorn', 'g2p_en', 'nltk', 'inflect', 'distance',
            'safetensors', 'huggingface_hub', 'multipart', 'faster_whisper', 'av', 'ctranslate2']:
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
        'phoneme_substitution', 'recording_quality', 'reference_audio', 'reference_audio_gui',
        'learning_contracts', 'repair_pipeline', 'segment_interpretation', 'number_review',
        'word_asr', 'analysis_jobs', 'analysis_client', 'caregiver_review_guidance', 'student_recording_library', 'api_diagnostics', 'bootstrap_server', 'android_recording_storage', 'server.android_recording_storage'])),
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='HearliumParentPC',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False,
               name='HearliumParentPC')
