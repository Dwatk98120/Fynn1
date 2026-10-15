# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# The launcher dispatches --server / --record / --pair in the same frozen EXE.
datas = []
binaries = []
hiddenimports = []
for pkg in ['torch', 'transformers', 'tokenizers', 'numpy', 'sounddevice', 'soundfile',
            'requests', 'fastapi', 'uvicorn', 'g2p_en', 'nltk', 'inflect', 'distance',
            'safetensors', 'huggingface_hub', 'multipart']:
    try:
        d, b, h = collect_all(pkg)
        datas.extend(d)
        binaries.extend(b)
        hiddenimports.extend(h)
    except Exception as exc:
        print('WARNING: optional collect_all failed for', pkg, exc)

# Include any non-Python model/data assets bundled with this project.
datas.extend(collect_data_files('certifi'))
a = Analysis(
    ['parent_pc_local/hearlium_launcher.py'],
    pathex=['parent_pc_local', 'server', '.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports + ['main', 'direct_recording', 'pair_phone',
        'hearlium_parent_pc_gui', 'temporal_prosody', 'candidate_word_engine',
        'learning_engine', 'learning_store', 'analysis_engine', 'phoneme_analysis',
        'phoneme_substitution', 'recording_quality'])),
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='HearliumParentPC',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False,
               name='HearliumParentPC')
