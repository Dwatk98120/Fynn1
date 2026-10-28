"""Verify Tk, new phoneme/capture code and historical guards in the frozen EXE."""
from types import CodeType
from PyInstaller.archive.readers import CArchiveReader


def strings(code):
    for value in code.co_consts:
        if isinstance(value, str):
            yield value
        elif isinstance(value, CodeType):
            yield from strings(value)


archive = CArchiveReader('dist/HearliumParentPC/HearliumParentPC.exe')
pyz = archive.open_embedded_archive('PYZ.pyz')
for module in ('tkinter', 'gui_smoke_check', 'ctc_segmentation', 'reference_phoneme_alignment',
               'phoneme_alignment_client', 'capture_identity', 'phoneme_hotfix_checks', 'pocketsphinx', 'legacy_alias_checks'):
    assert module in pyz.toc, f'Missing frozen module: {module}'
assert 'pyi_rth__tkinter' in archive.toc
for module in ('android_recording_storage', 'server.android_recording_storage'):
    values = set(strings(pyz.extract(module)))
    for marker in ('reanalysis_legacy_identity_unverified_requires_review',
                   'reanalysis_audio_identity_conflict', 'reanalysis_original_integrity_conflict'):
        assert marker in values, (module, marker)
for module in ('direct_recording', 'hearlium_parent_pc_gui'):
    assert any('Build 0.4.19 | Branch 2 | Legacy Recording Alias Repair' in value
               for value in strings(pyz.extract(module))), module
print('Frozen 0.4.19 modules, GUI and original reanalysis guards verified')

assert 'legacy-source-absent-alias-corroboration-v1' in set(strings(pyz.extract('server.android_recording_storage')))
