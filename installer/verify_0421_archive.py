"""Check release identity and receipt conflict guards in the frozen archive."""
from types import CodeType
from pathlib import Path
import sys
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
                   'capture_identity', 'phoneme_hotfix_checks', 'pocketsphinx', 'legacy_alias_checks',
                   'nltk_resources', 'server.nltk_resources', 'server.pc_copy_verification'):
        assert module in pyz.toc, module
    assert 'pyi_rth__tkinter' in archive.toc
    for module in ('android_recording_storage', 'server.android_recording_storage'):
        values = set(strings(pyz.extract(module)))
        for marker in ('reanalysis_source_identity_conflict', 'reanalysis_speaker_identity_conflict',
                       'reanalysis_recording_identity_conflict', 'reanalysis_audio_identity_conflict',
                       'reanalysis_original_integrity_conflict', 'legacy-source-absent-alias-corroboration-v1'):
            assert marker in values, (module, marker)
    for module in ('direct_recording', 'hearlium_parent_pc_gui'):
        assert any('Build 0.4.21 | Branch 2 | Offline Pronunciation and Safe Android Cleanup' in value
                   for value in strings(pyz.extract(module))), module
    assert '0.4.21' in set(strings(pyz.extract('reanalysis_integrity')))
    assert 'receiptConflictsRejected' in set(strings(pyz.extract('legacy_alias_checks')))
    assert '/v1/recording-preservation-check' in set(strings(pyz.extract('main')))
    assert 'android-local-audio-removal-v1' in set(strings(pyz.extract('server.pc_copy_verification')))
    assert 'cookies' in set(strings(pyz.extract('server.nltk_resources')))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from server.nltk_resources import validate_resources
    validate_resources('dist/HearliumParentPC/_internal/nltk_data')
    print('Frozen 0.4.21 release identity and receipt conflict guards verified')


if __name__ == '__main__':
    verify()
