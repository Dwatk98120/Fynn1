HEARLIUM ANDROID - CONSOLIDATED SOURCE PACKAGE (2026-10-17)
=========================================================
Source basis: Hearlium_Android_Send_Analyze_Visible_Button_Hotfix_20261017(3).zip

INCLUDED:
- Full source tree from the uploaded hotfix ZIP, including Android and Parent PC code
- MainActivity.kt with visible SEND & ANALYZE ON PC, uploadForAnalysis(), and Test PC Connection
- Gradle 8.9 configuration, Android Gradle Plugin 8.7.3, Kotlin 2.0.21
- New workflow .github/workflows/build-apk-recording-fix.yml for integration branch and main
- Existing .github/workflows/build-apk.yml retained from source for compatibility

IMPORTANT GRADLE SECURITY REPAIR:
The source ZIP's gradle/wrapper/gradle-wrapper.jar had SHA256:
d07579ef521a2867367fadeb0dc4f11fbcd9a9b90f9d0855dec04ee6cd8bd5a7
GitHub Actions rejected it as unknown. It has been REMOVED from this package.
The new workflow downloads official Gradle 8.9, regenerates the wrapper on GitHub,
then verifies SHA256 against the official Gradle 8.9 wrapper checksum:
498495120a03b9a6ab5d155f5de3c8f0d986a449153702fb80fc80e134484f17
The verified wrapper is NOT embedded in this ZIP because the official binary
was not available to download in this environment. The user has already
generated it locally and can upload it into gradle/wrapper/gradle-wrapper.jar.

HOW TO APPLY:
1. Extract this ZIP.
2. In GitHub, switch to hearlium-parent-pc-integration.
3. Upload the extracted files to repository root, preserving paths.
   For existing files, use Git/GitHub Desktop or another replacement-capable upload method.
4. IMPORTANT: Delete the rejected old gradle/wrapper/gradle-wrapper.jar from GitHub
   or replace it with the VERIFIED Gradle 8.9 JAR from your desktop repair folder.
   Do not leave the rejected JAR in the repository.
5. Check Actions for the new 'Hearlium Android APK - Verified Gradle 8.9' workflow.
6. If other existing workflows fail, review their separate configuration.

STATUS:
Source assembled and checked for the expected button and upload method.
Not compiled or runtime-tested here. Android upload/PC response still requires device testing.
