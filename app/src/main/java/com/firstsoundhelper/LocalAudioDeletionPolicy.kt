package com.firstsoundhelper

/** Pure policy, shared by the Android storage guard and JVM regression tests. */
internal object LocalAudioDeletionPolicy {
    data class Identity(val recordingId: String, val speakerId: String, val sha256: String, val bytes: Long)
    data class PcCopy(val protocol: String, val verified: Boolean, val identity: Identity,
                      val source: String, val nonce: String, val copies: Int)

    fun requireAllowed(local: Identity, receipt: PcCopy, expectedNonce: String,
                       caregiverConfirmed: Boolean, ageMillis: Long) {
        require(caregiverConfirmed) { "Caregiver confirmation is required" }
        requireVerifiedCopy(local, receipt, expectedNonce, ageMillis)
    }

    fun requireVerifiedCopy(local: Identity, receipt: PcCopy, expectedNonce: String, ageMillis: Long) {
        require(receipt.protocol == "android-local-audio-removal-v1" && receipt.verified && receipt.copies > 0) {
            "PC stored-copy verification is required; a transport receipt is insufficient"
        }
        require(local == receipt.identity && receipt.source == "android") { "PC copy identity/hash conflict" }
        require(expectedNonce.matches(Regex("^[a-f0-9]{32}$")) && receipt.nonce == expectedNonce) {
            "PC verification does not match this deletion request"
        }
        require(ageMillis in 0..30_000) { "PC verification expired; verify again" }
    }
}
