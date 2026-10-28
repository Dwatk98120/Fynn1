# Hearlium 0.4.21 / Android 3.3.4 validation, 2026-10-28

Source suite: **517 passed, 3 skipped**. Skips still require private original
adult WAVs/metadata. Test runs use temporary application-data roots and disabled
bytecode/pytest caches. The production Kotlin policy and recording store compiled with Kotlin 2.0.21,
JDK 17 and Gradle 8.9: **12 JUnit tests passed**, zero failures/errors. These are
real JVM policy/storage tests with real temporary-file IO and injected clocks;
not a claim of complete Android UI/device execution. A local Android clock stub
throws if accidentally used; no test may rely on a real Android clock. The local
harness initially needed that compile-time symbol, then all 12 tests passed.

The logged 0.4.20 failure occurred in NLTK's lazily loaded English JSON tagger
during pronunciation conversion. Earlier self-tests imported/constructed G2P
without calling it. The earlier frozen distribution/installer did include the
legacy tagger and CMU data, but installed-data inspection also found those
files absent on this PC. The supplied log cannot establish why they were absent.
User-cache fallback had masked the installed-data gap during earlier startup.

Build preparation now stages a pinned official resource set, validates archive
and individual-file SHA-256 values, and converts `cookies` through actual G2P.
The resulting phones were `K UH1 K IY0 Z`. This is a software execution probe,
not recognition/pronunciation accuracy or pediatric clinical validation.
Frozen execution restricts NLTK lookup to verified bundled assets. Missing or
changed resources fail before models are advertised as ready. The frozen
self-test exercises the same lazy conversion path.

Regression coverage includes missing English JSON/CMU resources, modified
resource bytes, propagation of lazy-converter failures, empty conversion output,
read-only PC copy verification, every same-ID conflicting copy, absent/damaged
audio, transport-only receipts and unreadable metadata. Kotlin tests cover
caregiver refusal, stale/replayed receipts and recording/speaker/source/size/hash
conflicts. Structural guards bind single/bulk/privacy UI removal to the same
tested policy and preserve metadata/approval history. Synthetic fixtures are
the only files removed or deliberately damaged by tests.

The PC preservation-check endpoint is independent of learning approval. It
checks stored originals and original metadata without rewriting them. Android
first verifies all selected copies, then asks for caregiver confirmation and
checks each PC copy again immediately before removing that phone WAV. Request
nonces bind responses to the current attempt; monotonic freshness is limited
to 30 seconds. The phone retains metadata, labels, all analyses and immutable
removal request/completion events. Legacy/unverifiable copies remain protected.

The installed 0.4.20 executable was SHA-256 matched before a separate repair
added three missing English JSON files. A subsequent administrator prompt for
the remaining corpus assets was canceled; a complete installed-data-only
pronunciation check did not pass for that installation. No further elevation
was attempted. `installer/repair_installed_nltk_data.ps1` remains a guarded
repair option for that exact 0.4.20 executable. New installation should use the
complete 0.4.21 installer; installation is a separate user action.

See SOURCE_RELEASE_0.4.21_VERIFICATION.json and the separate installer validation
JSON for the exact current frozen-check, executable, installer and source hashes.
All prior 0.4.20 release artifacts remain historical. No original recordings,
metadata, learning approvals or audit history were overwritten, renamed or
deleted. No installed service was stopped or restarted by these changes.

GitHub Actions must still compile the complete APK, and physical-device
acceptance remains pending. Test backup verification, cancellation, damaged
copies, network loss, offline restart, capture/upload exclusion during cleanup,
single/bulk cleanup and retained PC/phone history using disposable data.
Check existing signing-key compatibility before updating an Android device.
Local policy compilation does not establish a successful remote APK build.
