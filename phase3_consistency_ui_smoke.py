"""Run with Xvfb; no microphones or network requests required."""
import json, os, sys, tempfile, types
from pathlib import Path
from unittest import mock

with tempfile.TemporaryDirectory() as t:
    os.environ['LOCALAPPDATA'] = t
    os.environ['FSH_RECORDINGS_DIR'] = str(Path(t) / 'Hearlium' / 'ParentPC' / 'recordings')
    sys.modules['sounddevice'] = types.ModuleType('sounddevice')
    sys.path[:0] = [str(Path(__file__).parent/'parent_pc_local'),str(Path(__file__).parent/'server')]
    import direct_recording as dr
    from android_recording_storage import store_android_recording
    data = {'recordingId':'sample-original','observation':{'observationId':'test-obs-1'},
            'wordRecognition':{'text':'I want three cookies', 'status':'candidate_transcription'},
            'numberReview': {'segments':[]}}
    files = store_android_recording(b'unchanged example input', 'sample-original', 'student-demo', 'session-demo', data)
    app = dr.DirectRecorder()
    app.withdraw()
    app.update_idletasks()
    app.refresh_history()
    items = app.history.get_children()
    assert len(items) == 1, items
    iid = items[0]
    app.history.selection_set(iid)
    app.load_selected_into_review()
    assert app.last_result is not None
    assert app.last_result['wordRecognition']['text'] == 'I want three cookies'
    assert 'I want three cookies' in app.result_box.get('1.0','end')
    assert app._history_cached_rows[0]['word'] == 'I want three cookies'
    app.history_search.set('three cookies')
    assert len(app.history.get_children()) == 1
    observed = []
    class StubThread:
        def __init__(self, target, args, daemon): self.args=args
        def start(self): observed.append((app.last_result, app._analysis_in_flight, self.args[1]))
    prev_generation = app._analysis_generation
    with mock.patch.object(dr.threading, 'Thread', StubThread):
        app.analyze_recording()
    assert app._analysis_generation == prev_generation + 1
    assert app.last_result is None
    assert observed and observed[0][0] is None and observed[0][1]
    assert 'Analysis in progress' in app.approval_status.get()
    app.destroy()
    print('LIVE GUI SMOKE PASSED: Android export review, search and analysis invalidation')
