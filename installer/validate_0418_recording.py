"""Read-only offline replay of an existing recording for the 0.4.18 hotfix.

This deliberately bypasses server endpoints and _analyze_audio_sync, whose
normal responsibilities include persisting recordings/observations. Only an
explicit workspace JSON report and isolated workspace runtime folders are made.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wav_snapshot(folder):
    folder = Path(folder)
    return {str(path.relative_to(folder)): digest_file(path)
            for path in sorted(folder.rglob("*.wav")) if path.is_file()}


def compare_snapshot(before, after):
    return {
        "beforeCount": len(before), "afterCount": len(after),
        "addedWavs": sorted(after.keys() - before.keys()),
        "missingWavs": sorted(before.keys() - after.keys()),
        "changedWavs": sorted(name for name in before.keys() & after.keys()
                              if before[name] != after[name]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wav", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", help="Explicitly human-confirmed spoken text; no automatic reference")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.suffix.lower() != ".json" or not output.is_relative_to(ROOT / "reports"):
        parser.error("--output must be a JSON file inside this workspace's reports directory")
    wav, metadata_path = args.wav.resolve(), args.metadata.resolve()
    if not wav.is_file() or not metadata_path.is_file():
        parser.error("Original WAV and saved metadata must both exist")
    if output in (wav, metadata_path):
        parser.error("Report cannot replace recording evidence")

    isolated = ROOT / "reports" / "validate_0418_isolated"
    # Set these before any Hearlium imports. Do not read a production learning
    # profile or permit module initialization to use production application data.
    os.environ["LOCALAPPDATA"] = str(isolated / "appdata")
    os.environ["FSH_DATA_DIR"] = str(isolated / "learning")
    os.environ["FSH_RECORDINGS_DIR"] = str(isolated / "recordings")
    os.environ["PHONEME_MODEL"] = str(ROOT / "models" / "phoneme-wav2vec2")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "server"))

    before = wav_snapshot(wav.parent)
    metadata_before = digest_file(metadata_path)
    raw = wav.read_bytes()
    original_digest = hashlib.sha256(raw).hexdigest()
    prior = json.loads(metadata_path.read_text(encoding="utf-8"))
    saved = prior.get("analysisResult") or {}
    report = {
        "checkedUtc": datetime.now(timezone.utc).isoformat(),
        "build": "0.4.18", "mode": "read_only_offline_replay",
        "recordingFile": wav.name, "metadataFile": metadata_path.name,
        "originalSha256Before": original_digest,
        "metadataSha256Before": metadata_before,
        "sourceRecordingDirectory": str(wav.parent),
        "learningProfile": "isolated_empty_profile",
        "sourceAudioModified": False, "productionServerInvoked": False,
        "referenceConditionedAlignmentRequested": bool(args.reference),
        "boundaryAccuracy": None,
        "boundaryAccuracyStatus": "requires_manually_verified_phoneme_boundaries",
    }
    error = None
    try:
        import io
        import soundfile as sf
        import torch
        import main as server_main
        from server.ctc_segmentation import phoneme_confidences, propose_boundary_alternatives
        from server.word_phoneme_alignment_review import review_word_phoneme_alignment

        torch.set_num_threads(min(4, os.cpu_count() or 1))
        samples, sample_rate = sf.read(io.BytesIO(raw), dtype="float32")
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        if sample_rate != 16000:
            raise ValueError("Existing 16 kHz WAV required; benchmark never converts or writes audio")
        server_main.load_models()
        with torch.inference_mode():
            inputs = server_main.processor(samples, sampling_rate=16000, return_tensors="pt")
            logits = server_main.model(inputs.input_values.to(server_main.DEVICE)).logits
        decoded, raw_tokens, raw_confidences = server_main.decode_ctc_with_confidence(logits)
        segments = server_main.segment_ctc_phonemes(logits, len(samples) / sample_rate)
        acoustic = server_main.acoustic_features(samples, sample_rate)
        temporal = server_main.temporal_features(samples, sample_rate)
        vocabulary = server_main.candidate_words()

        @lru_cache(maxsize=None)
        def ipa_for(word):
            return server_main.g2p_ipa(word)

        candidates = []
        for segment in segments:
            units = server_main.tokenize_ipa(segment["phonemes"])
            confidence = phoneme_confidences(segment, server_main.tokenize_ipa)
            ranked = []
            if len(units) <= 14:
                ranked = server_main.rank_candidate_words(
                    words=vocabulary, observed_ipa=segment["phonemes"],
                    observed_tokens=units, observed_confidences=confidence,
                    observed_text=segment["phonemes"], context=str(prior.get("context") or ""),
                    profile={}, g2p_ipa=ipa_for, tokenize_ipa=server_main.tokenize_ipa,
                    evidence_scores=server_main.evidence_scores,
                    combined_confidence=server_main.combined_confidence,
                    acoustic=acoustic, temporal=temporal,
                    build_learning_layers=server_main.build_learning_layers, max_results=3)
            candidates.append({
                "segmentIndex": segment["index"], "phonemes": segment["phonemes"],
                "startSeconds": segment["startSeconds"], "endSeconds": segment["endSeconds"],
                "topCandidates": [entry["word"] for entry in ranked],
                "candidateScores": [entry["confidence"] for entry in ranked],
                "phonemeTokens": units, "phonemeConfidences": confidence,
                "confidenceCountMatchesPhonemes": len(confidence) == len(units),
                "confidenceValuesAreNotAccuracy": True,
            })
        alignment_review = review_word_phoneme_alignment(saved.get("wordRecognition") or {}, segments)
        alternatives = propose_boundary_alternatives(segments, allow_disputed_delimiters=True)
        saved_raw = saved.get("transcript", (saved.get("observation") or {}).get("transcript"))
        report.update({
            "durationSeconds": len(samples) / sample_rate,
            "sampleRate": sample_rate, "device": server_main.DEVICE,
            "rawDecoderMatchesSavedTranscript": decoded == saved_raw,
            "rawDecodedTranscript": decoded, "savedRawTranscript": saved_raw,
            "rawDecodedTokenCount": len(raw_tokens), "rawDecodedConfidenceCount": len(raw_confidences),
            "segmentCount": len(segments),
            "segmentEmissionTokenCount": sum(len(s.get("tokenEvidence") or []) for s in segments),
            "tokenConfidenceMappingComplete": all(
                item["confidenceCountMatchesPhonemes"] and
                all(value is not None for value in item["phonemeConfidences"])
                for item in candidates),
            "tokenTimingEvidence": segments,
            "newCandidateRanking": candidates,
            "wantInCandidateVocabulary": "want" in vocabulary,
            "wantTopCandidateSegments": [item["segmentIndex"] for item in candidates
                                         if item["topCandidates"][:1] == ["want"]],
            "groupedTimingReview": alignment_review,
            "boundaryAlternativeCount": len(alternatives),
            "boundaryAlternatives": alternatives,
            "savedWhisperHypothesisReusedWithoutInference": True,
            "independentRecognitionAccuracy": None,
            "remainingUncertainty": "No boundary alternative is automatically selected. "
                                    "The final sentence may retain fragmented independent phoneme output. "
                                    "No pronunciation or target-speaker identity is verified.",
        })
        if args.reference:
            from server.reference_phoneme_alignment import align_reference_bytes
            report["referenceConditionedAlignment"] = align_reference_bytes(
                raw, args.reference, human_confirmed=True)
    except Exception as exc:
        error = exc
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        after = wav_snapshot(wav.parent)
        difference = compare_snapshot(before, after)
        report.update({
            "originalSha256After": digest_file(wav),
            "metadataSha256After": digest_file(metadata_path),
            "recordingWavIntegrity": difference,
            "wavSnapshotBeforeSha256": before, "wavSnapshotAfterSha256": after,
        })
        report["originalUnchanged"] = report["originalSha256After"] == original_digest
        report["metadataUnchanged"] = report["metadataSha256After"] == metadata_before
        report["allRecordingWavsUnchanged"] = not any(
            difference[key] for key in ("addedWavs", "missingWavs", "changedWavs"))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False)
    success = error is None and all(report[key] for key in (
        "originalUnchanged", "metadataUnchanged", "allRecordingWavsUnchanged"))
    print(json.dumps({"passed": success, "report": str(output),
                      "wantTopCandidateSegments": report.get("wantTopCandidateSegments"),
                      "boundaryAlternativeCount": report.get("boundaryAlternativeCount"),
                      "rawDecoderMatchesSavedTranscript": report.get("rawDecoderMatchesSavedTranscript"),
                      "error": report.get("error")}, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
