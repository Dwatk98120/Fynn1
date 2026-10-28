package com.firstsoundhelper

import org.junit.Assert.*
import org.junit.Test

class AndroidBuildInfoTest {
    @Test fun displaysArtifactValuesRatherThanExpectedReleaseConstants() {
        val info = AndroidBuildInfo.format("test-version", 123, "release", "test-gradle", "test-agp", "timeZ", "commit")
        assertTrue(info.contains("Android test-version (123) • release"))
        assertTrue(info.contains("Gradle test-gradle • AGP test-agp"))
        assertTrue(info.contains("Built UTC: timeZ"))
        assertTrue(info.contains("Commit: commit"))
    }
    @Test fun unavailableValuesAreExplicit() {
        val info = AndroidBuildInfo.format("test", 1, "debug", "", "", "", "")
        assertTrue(info.contains("Gradle Unavailable • AGP Unavailable"))
        assertTrue(info.contains("Commit: Unavailable"))
    }
}
