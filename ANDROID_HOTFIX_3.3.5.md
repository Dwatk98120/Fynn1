# Android 3.3.5 / code11 — visible removal confirmation

The supplied phone screenshots showed successful PC-copy verification followed
by a confirmation offering only “Keep local audio.” The removal callback existed
but its standard AlertDialog action was not visible on that device. The old
confirmation relied on the OEM system button area and shared popup styling that
increased button padding/minimum height.

This hotfix uses a dedicated confirmation with two stacked, full-width actions:
**Remove local audio** and **Keep local audio**. The explanation scrolls while
both actions stay visible. Labels wrap without ellipsizing. The confirmation
does not enter the generic popup restyler. Keeping, canceling or dismissing never
authorizes removal; an explicit removal tap can invoke the callback only once.
Status text distinguishes verified copies, the pending choice, and rechecking.

The safety workflow remains unchanged: check stored PC copies, ask the caregiver,
then recheck each copy before removing only the matching local WAV. Recording ID,
speaker/source, byte size, SHA-256, fresh nonce and receipt age must pass. Phone
metadata, labels, analyses and removal audits remain; PC originals remain intact.
No recordings were removed from a real device during this work.

The previously requested build-information backlog item is also implemented on
the main screen: actual APK version/code/build type, Gradle and AGP versions,
build time in UTC, and commit identifier when available. Values come from the
generated BuildConfig, not expected-version labels. Missing commit data is
explicitly marked “Unavailable.” Parent PC stays at 0.4.21.

Validation:

- 18 JVM tests passed: 4 Robolectric UI tests, 5 deletion-policy tests, 7 real
  temporary-file recording-store tests and 2 build-information formatter tests.
- UI checks cover 320dp portrait, 200% text scaling, landscape with large text,
  complete button bounds/labels, no action overlap, safe keeping and single-tap
  confirmation. The simulator screen setup was corrected from zero dimensions
  before these layout results were accepted. Simulated SDK: Android API 28.
- 11 Python source/wiring checks and the Android source guard passed.
- The actual Android Gradle configuration and `generateDebugBuildConfig` tasks
  passed using JDK 17, Gradle 8.9 and AGP 8.7.3. Generated values were version
  3.3.5/code11, Gradle 8.9 and AGP 8.7.3. The local commit was unavailable.
- Parent PC program-source hashes are checked against the historical 0.4.21
  build proof; its backend was not changed or rebuilt for this Android hotfix.

Complete APK compilation, signing compatibility and physical Samsung-device
acceptance remain pending. The local JVM harness compiles the production dialog,
formatter, policy and recording-store classes; it does not compile/run the whole
MainActivity or replace on-device testing. GitHub runs `testDebugUnitTest` and
`assembleDebug`, followed by the compiled-APK feature guard, before publication
of its artifact. Test removal on disposable recordings first. Do not uninstall
or clear app data to force an APK update when signing keys differ.

Earlier 0.4.21/Android 3.3.4 validation files are retained as historical evidence.
Current Android results are in ANDROID_3.3.5_VALIDATION.json. No installation,
GitHub push, Main changes or modification of original recording/approval/audit
data was performed. Tests only damage/remove their own synthetic temporary files.

UI-test framework reference: [Robolectric configuration](https://robolectric.org/configuring/).
