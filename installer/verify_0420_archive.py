"""Check release identity and receipt conflict guards in the frozen archive."""
from types import CodeType
from PyInstaller.archive.readers import CArchiveReader


def strings(code):
    for value in (code.co_consts if isinstance(code, CodeType) else code):
        if isinstance(value, str):
            yield value
        elif isinstance(value, (CodeType, tuple)):
            yield from strings(value)


def verify():
    archive = CArchiveReader('dist/HearliumParentPC/HearliumParentPC.exe')
    pyz = archive.open_embedded_archive('PYZ.pyz')
    for module in ('tkinter', 'gui_smoke_check', 'ctc_segmentation',
                   'reference_phoneme_alignment', 'phoneme_alignment_client',
                   'capture_identity', 'phoneme_hotfix_checks', 'pocketsphinx', 'legacy_alias_checks'):
        assert module in pyz.toc, module
    assert 'pyi_rth__tkinter' in archive.toc
    for module in ('android_recording_storage', 'server.android_recording_storage'):
        values = set(strings(pyz.extract(module)))
        for marker in ('reanalysis_source_identity_conflict', 'reanalysis_speaker_identity_conflict',
                       'reanalysis_recording_identity_conflict', 'reanalysis_audio_identity_conflict',
                       'reanalysis_original_integrity_conflict', 'legacy-source-absent-alias-corroboration-v1'):
            assert marker in values, (module, marker)
    for module in ('direct_recording', 'hearlium_parent_pc_gui'):
        assert any('Build 0.4.20 | Branch 2 | Reanalysis Receipt Integrity Repair' in value
                   for value in strings(pyz.extract(module))), module
    assert '0.4.20' in set(strings(pyz.extract('reanalysis_integrity')))
    assert 'receiptConflictsRejected' in set(strings(pyz.extract('legacy_alias_checks')))
    print('Frozen 0.4.20 release identity and receipt conflict guards verified')


if __name__ == '__main__':
    verify()
