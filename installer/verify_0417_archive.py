"""Verify release markers in the actual frozen Python archive."""
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
for module in ('tkinter', 'tkinter.ttk', 'tkinter.filedialog',
               'tkinter.messagebox', 'tkinter.font', 'gui_smoke_check'):
    assert module in pyz.toc, f'Missing frozen GUI module: {module}'
assert 'pyi_rth__tkinter' in archive.toc, 'Missing Tk runtime data-path hook'
for module in ('android_recording_storage', 'server.android_recording_storage'):
    values = set(strings(pyz.extract(module)))
    assert 'reanalysis_legacy_identity_unverified_requires_review' in values, module
    assert 'reanalysis_audio_identity_conflict' in values, module
    assert 'reanalysis_original_integrity_conflict' in values, module
for module in ('direct_recording', 'hearlium_parent_pc_gui'):
    assert any('Build 0.4.17 | Branch 2 | Legacy Checksum Reanalysis Repair' in s
               for s in strings(pyz.extract(module))), module
print('Frozen 0.4.17 archive modules and legacy checksum guards verified')
