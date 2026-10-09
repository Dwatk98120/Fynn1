# First Sound Helper — Android Studio Ready Trial v3

This package is the Android Studio trial build with the missing Gradle wrapper added.

## Open in Android Studio
1. Extract this ZIP.
2. Open the folder containing `settings.gradle` and `build.gradle` (the project root).
3. Let Gradle sync using the included wrapper.
4. If Android Studio asks for a Gradle JDK, use JDK 17 or a compatible newer JDK.
5. Run the `app` configuration on an Android 8.0+ device/emulator.

## Parent PC local backend
The default API is:
`[removed-cloud-backend]`

To use another backend, put this in the root `gradle.properties`:
`PARENT_PC_LOCAL_API_URL=https://YOUR-API-URL`

The Android app reads this into `BuildConfig.API_BASE_URL` at build time.

## Important
This is a trial engineering build. The AI confidence/evidence values are engineering signals, not clinical measurements or diagnoses. The Parent PC local service must be deployed and reachable for cloud analysis.
