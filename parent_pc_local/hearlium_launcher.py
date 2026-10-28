from __future__ import annotations
import os
import sys
import logging
import time
import traceback
import faulthandler
import threading
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
APP_ROOT = Path(sys.executable).resolve().parent if FROZEN else BUNDLE_ROOT
USER_DATA = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Hearlium" / "ParentPC"
USER_DATA.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("FSH_DATA_DIR", str(USER_DATA / "learning"))
os.environ.setdefault("FSH_RECORDINGS_DIR", str(USER_DATA / "recordings"))
for folder in (BUNDLE_ROOT / "server", BUNDLE_ROOT / "parent_pc_local", BUNDLE_ROOT):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

def _server_heartbeat():
    from api_diagnostics import write_event
    began = time.monotonic()
    while True:
        time.sleep(60)
        write_event("server_heartbeat", uptimeSeconds=round(time.monotonic() - began, 1))


def _server_protocol_settings():
    """Use only protocols the local HTTP API actually serves.

    Uvicorn's automatic WebSocket selection imports optional modules such as
    websockets.legacy at runtime. A frozen executable can pass static import
    checks and still fail during server startup if those modules were not
    collected. Hearlium currently provides HTTP endpoints, not WebSocket
    endpoints, so disable unused WebSockets and select bundled h11 directly.
    """
    return {"ws": "none", "http": "h11", "loop": "asyncio"}


def run_server():
    import uvicorn
    import bootstrap_server
    # Windowed PyInstaller apps may have sys.stdout/sys.stderr set to None.
    # Avoid Uvicorn's default console formatter, which calls .isatty().
    log_path = USER_DATA / "parent_pc_server.log"
    # PyInstaller's Windows GUI executable normally provides no stdout/stderr.
    # Redirect Python-level tracebacks to a persistent local console log.
    console_path = USER_DATA / "parent_pc_server_console.log"
    if sys.stdout is None:
        sys.stdout = open(console_path, "a", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = open(console_path, "a", encoding="utf-8", buffering=1)
    logging.basicConfig(filename=str(log_path), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        force=True)
    from api_diagnostics import write_event
    crash_file = open(USER_DATA / "parent_pc_server_fatal.log", "a", encoding="utf-8", buffering=1)
    try:
        faulthandler.enable(file=crash_file, all_threads=True)
    except (ValueError, OSError):
        pass
    write_event("server_bootstrap_started", port=8000)
    logging.info("Starting lightweight Hearlium API bootstrap on port 8000; pid=%s", os.getpid())
    threading.Thread(target=_server_heartbeat, name="HearliumDiagnosticsHeartbeat", daemon=True).start()
    try:
        uvicorn.run(bootstrap_server.app, host="0.0.0.0", port=8000,
                    reload=False, log_level="info", log_config=None, access_log=False,
                    **_server_protocol_settings())
    except BaseException as exc:
        logging.exception("Local API terminated with an exception")
        write_event("server_exception", errorType=type(exc).__name__,
                    winerror=getattr(exc, "winerror", None))
        raise
    finally:
        logging.warning("API server loop exited")
        write_event("server_loop_exited")

def run_recorder(initial_tab="record"):
    from direct_recording import DirectRecorder
    window = DirectRecorder(initial_tab=initial_tab)
    window.protocol("WM_DELETE_WINDOW", window.on_close)
    window.mainloop()

def run_pair():
    from pair_phone import PairPhone
    PairPhone().mainloop()

def self_test():
    from nltk_resources import configure_resources, verify_pronunciation
    configure_resources(required=True)
    verify_pronunciation()
    from legacy_alias_checks import run_check as check_legacy_aliases
    check_legacy_aliases()
    from phoneme_hotfix_checks import run_check as check_phonemes
    check_phonemes()
    from gui_smoke_check import run_check as check_gui
    check_gui()
    from speech_hotfix_checks import run_check as check_speech_hotfix
    from upload_retry_check import run_check as check_upload_retry
    check_speech_hotfix()
    check_upload_retry()
    import torch, transformers, sounddevice, soundfile, fastapi, uvicorn, g2p_en
    import bootstrap_server
    # Test Uvicorn's *dynamic protocol imports* inside the actual frozen EXE.
    # Basic `import uvicorn` checks missed the startup crash on Windows.
    server_config = uvicorn.Config(bootstrap_server.app, log_config=None,
                                   **_server_protocol_settings())
    server_config.load()
    if server_config.ws_protocol_class is not None:
        raise RuntimeError("Frozen server unexpectedly enabled WebSockets")
    import io
    import numpy as np
    # Decode an in-memory WAV, and test the PyAV codec used by Faster-Whisper.
    buffer = io.BytesIO()
    soundfile.write(buffer, np.zeros(1600, dtype=np.float32), 16000, format="WAV")
    buffer.seek(0)
    decoded, rate = soundfile.read(buffer, dtype="float32")
    assert rate == 16000 and len(decoded) == 1600
    import main as server_main
    assert server_main.app is not None
    from temporal_prosody import analyze_temporal_prosody
    assert callable(analyze_temporal_prosody)
    import av, ctranslate2, faster_whisper
    buffer.seek(0)
    with av.open(buffer, mode="r", format="wav") as container:
        assert next(container.decode(audio=0)).samples > 0
    from word_asr import transcribe_words
    assert callable(transcribe_words)
    import inspect
    assert "recording_source" in inspect.signature(server_main._analyze_audio_sync).parameters
    verify_layer2_activity()
    print("Hearlium imports, frozen Uvicorn protocol load, PyAV and Faster-Whisper OK")


def verify_layer2_activity():
    """Check that THIS running executable contains the Layer 2 evidence code.

    This uses generated audio only; it does not modify recordings or learning.
    A nonzero exit status lets the installer builder reject a stale executable.
    """
    import numpy as np
    from analysis_engine import acoustic_features, temporal_features

    sample_rate = 16000
    samples = np.concatenate((
        np.full(int(sample_rate * 0.4), 0.08, dtype=np.float32),
        np.zeros(int(sample_rate * 1.0), dtype=np.float32),
    ))
    acoustic = acoustic_features(samples, sample_rate)
    temporal = temporal_features(samples, sample_rate)
    for evidence in (acoustic, temporal):
        if evidence.get("activityEvidenceVersion") != "layer2-activity-tail-v2":
            raise RuntimeError("Frozen executable is missing Layer 2 activity evidence")
        if evidence.get("activityEstimateIsVerifiedSpeech") is not False:
            raise RuntimeError("Layer 2 activity uncertainty disclosure is missing")
        trailing = evidence.get("trailingQuietSeconds")
        if not isinstance(trailing, (int, float)) or not 0.9 <= trailing <= 1.1:
            raise RuntimeError("Layer 2 fails to separate synthetic trailing silence")
    if acoustic.get("activityTailEnergyRatio") is None:
        raise RuntimeError("Layer 2 acoustic activity-tail measurement is missing")
    late_weak = np.concatenate((
        np.full(int(sample_rate * 0.4), 0.08, dtype=np.float32),
        np.zeros(int(sample_rate * 1.1), dtype=np.float32),
        np.full(int(sample_rate * 0.08), 0.012, dtype=np.float32),
        np.zeros(int(sample_rate * 0.2), dtype=np.float32),
    ))
    late_result = acoustic_features(late_weak, sample_rate)
    if (late_result["estimatedActivityEndSeconds"] is None
            or late_result["estimatedActivityEndSeconds"] >= 0.5
            or late_result["weakLateActivityIslandCount"] < 1):
        raise RuntimeError("Layer 2 overestimated speech duration after weak late activity")
    ambiguous = np.concatenate((
        np.full(int(sample_rate * 0.4), 0.08, dtype=np.float32),
        np.zeros(int(sample_rate * 1.1), dtype=np.float32),
        np.full(int(sample_rate * 0.45), 0.07, dtype=np.float32),
    ))
    uncertain = acoustic_features(ambiguous, sample_rate)
    if (uncertain["activityEstimationStatus"] != "ambiguous_separated_activity_islands"
            or uncertain["estimatedActivityEndSeconds"] is not None):
        raise RuntimeError("Layer 2 must disclose significant separated speech uncertainty")
    from speech_activity_review import review_speech_activity, REVIEW_VERSION
    review = review_speech_activity(
        {"durationSec": 6.0, "lastDetectedEnergyActivitySeconds": 5.8},
        {"status": "candidate_transcription",
         "segments": [{"start": 0.4, "end": 2.0, "text": "hello"}]},
        [{"startSeconds": 0.5, "endSeconds": 5.7, "phonemes": "hɛloʊ"}],
    )
    if (REVIEW_VERSION != "layer2-speech-ambient-crosscheck-v1"
            or review["status"] != "recognizer_timing_disagreement_review"
            or review["candidateSpeechEndSeconds"] is not None
            or review["changesProtectedObservation"] is not False):
        raise RuntimeError("Frozen EXE is missing safe Layer 2 recognizer disagreement review")
    from speech_activity_review import review_speaker_source, SOURCE_REVIEW_VERSION
    source_review = review_speaker_source(
        review, {"uncorroboratedLateSegmentCount": 3,
                 "automaticWordSuggestionHoldCount": 3})
    if (SOURCE_REVIEW_VERSION != "layer2-target-speaker-attribution-v1"
            or source_review["status"] != "late_audio_source_unverified_human_review"
            or source_review["targetSpeakerIdentityVerified"] is not False
            or source_review["backgroundSingingConfirmedByModel"] is not False
            or source_review["learningEligible"] is not False):
        raise RuntimeError("Frozen EXE is missing the target-speaker attribution warning")
    from phoneme_timing_review import review_phoneme_timing, REVIEW_VERSION as TIMING_VERSION
    timing = review_phoneme_timing(
        np.concatenate((np.full(sample_rate, .05, dtype=np.float32),
                        np.zeros(3 * sample_rate, dtype=np.float32))), sample_rate,
        {"status": "candidate_transcription", "segments": [
            {"start": 0.1, "end": 0.7, "text": "hello"}]},
        [{"index": 0, "startSeconds": 0.1, "endSeconds": 0.8, "phonemes": "hɛloʊ"},
         {"index": 1, "startSeconds": 3.2, "endSeconds": 3.8, "phonemes": "a"}],
    )
    if (TIMING_VERSION != "layer23-boundary-phoneme-reliability-v1"
            or timing["status"] != "late_phoneme_timing_disagreement_review"
            or timing["uncorroboratedLateSegmentIndices"] != [1]
            or timing["automaticWordSuggestionHoldIndices"] != [1]
            or timing["ambientSoundConfirmed"] is not False
            or timing["changesProtectedObservation"] is not False):
        raise RuntimeError("Frozen EXE is missing Layer 2/3 phoneme-timing safety review")
    if (timing.get("postWordEnergyReviewVersion") != "layer2-post-word-energy-review-v1"
            or timing.get("postWordRatioIsSpeechOrSpeakerEvidence") is not False):
        raise RuntimeError("Frozen EXE is missing the cautious post-word energy diagnostic")
    # The Parent PC job must never be mislabeled as an Android upload.
    import inspect
    from android_recording_storage import store_android_recording
    if "source" not in inspect.signature(store_android_recording).parameters:
        raise RuntimeError("Frozen EXE is missing recording-origin preservation")
    return True

def run_gui():
    from hearlium_parent_pc_gui import HearliumParentPC
    HearliumParentPC().mainloop()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    mode = sys.argv[1] if len(sys.argv) > 1 else "--gui"
    if mode == "--server": run_server()
    elif mode == "--record": run_recorder()
    elif mode == "--record-history": run_recorder(initial_tab="history")
    elif mode == "--pair": run_pair()
    elif mode == "--self-test": self_test()
    elif mode == "--gui-smoke-test":
        import json
        from gui_smoke_check import run_check
        report = run_check()
        Path(sys.argv[2]).write_text(json.dumps(report, indent=2), encoding="utf-8")
    elif mode == "--align-phonemes":
        from phoneme_alignment_client import main
        sys.exit(main(sys.argv[2:]))
    elif mode == "--verify-layer2": verify_layer2_activity()
    elif mode == "--verify-phoneme-hotfix":
        import json
        from phoneme_hotfix_checks import run_check
        Path(sys.argv[2]).write_text(json.dumps(run_check(), indent=2), encoding='utf-8')
    elif mode == '--verify-legacy-alias':
        import json
        from legacy_alias_checks import run_check
        Path(sys.argv[2]).write_text(json.dumps(run_check(), indent=2), encoding='utf-8')
    elif mode == "--verify-android-retry":
        import json
        from upload_retry_check import run_check
        report = run_check()
        destination = USER_DATA / 'analysis_results' / 'upload_retry_check_0.4.17.json'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    else: run_gui()
