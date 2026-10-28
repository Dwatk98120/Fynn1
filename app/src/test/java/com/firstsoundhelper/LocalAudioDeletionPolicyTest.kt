package com.firstsoundhelper

import org.junit.Assert.assertThrows
import org.junit.Test

class LocalAudioDeletionPolicyTest {
    private val local = LocalAudioDeletionPolicy.Identity("r1", "s1", "a".repeat(64), 100)
    private val nonce = "b".repeat(32)
    private val pc = LocalAudioDeletionPolicy.PcCopy("android-local-audio-removal-v1", true, local, "android", nonce, 1)

    @Test fun matchingFreshCopyWithCaregiverConfirmationIsAllowed() {
        LocalAudioDeletionPolicy.requireAllowed(local, pc, nonce, true, 0)
    }

    @Test fun caregiverConfirmationIsRequired() {
        assertThrows(IllegalArgumentException::class.java) {
            LocalAudioDeletionPolicy.requireAllowed(local, pc, nonce, false, 0)
        }
    }

    @Test fun transportReceiptAndMissingCopyAreBlocked() {
        for (invalid in listOf(pc.copy(protocol = "transport"), pc.copy(verified = false), pc.copy(copies = 0))) {
            assertThrows(IllegalArgumentException::class.java) {
                LocalAudioDeletionPolicy.requireAllowed(local, invalid, nonce, true, 0)
            }
        }
    }

    @Test fun identitySourceAndHashConflictsAreBlocked() {
        val conflicts = listOf(pc.copy(source = "parent_pc"), pc.copy(identity = local.copy(recordingId = "other")),
            pc.copy(identity = local.copy(speakerId = "other")), pc.copy(identity = local.copy(sha256 = "0".repeat(64))),
            pc.copy(identity = local.copy(bytes = 101)))
        for (invalid in conflicts) assertThrows(IllegalArgumentException::class.java) {
            LocalAudioDeletionPolicy.requireAllowed(local, invalid, nonce, true, 0)
        }
    }

    @Test fun replayedOrExpiredProofIsBlocked() {
        for (age in listOf(-1L, 30_001L)) assertThrows(IllegalArgumentException::class.java) {
            LocalAudioDeletionPolicy.requireAllowed(local, pc, nonce, true, age)
        }
        assertThrows(IllegalArgumentException::class.java) {
            LocalAudioDeletionPolicy.requireAllowed(local, pc.copy(nonce = "c".repeat(32)), nonce, true, 0)
        }
    }
}
