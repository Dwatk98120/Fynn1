package com.firstsoundhelper

internal object AndroidBuildInfo {
    fun format(versionName: String, versionCode: Int, buildType: String, gradle: String,
               agp: String, builtUtc: String, commit: String): String {
        fun available(value: String) = value.ifBlank { "Unavailable" }
        return "Android $versionName ($versionCode) • ${available(buildType)}\n" +
            "Gradle ${available(gradle)} • AGP ${available(agp)}\n" +
            "Built UTC: ${available(builtUtc)}\nCommit: ${available(commit)}"
    }
}
