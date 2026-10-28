package com.firstsoundhelper

import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class LocalSpeechRecordingRemovalTest {
    @get:Rule val temporary = TemporaryFolder()
    private val nonce = "b".repeat(32)

    private fun wav(): ByteArray = ByteBuffer.allocate(64).order(ByteOrder.LITTLE_ENDIAN).apply {
        put("RIFF".toByteArray()); putInt(56); put("WAVEfmt ".toByteArray()); putInt(16)
        putShort(1); putShort(1); putInt(16000); putInt(32000); putShort(2); putShort(16)
        put("data".toByteArray()); putInt(20); put(ByteArray(20))
    }.array()

    private fun fixture(clock: () -> Long = { 1000L }): Pair<LocalSpeechRecordingStore, LocalSpeechRecording> {
        val store = LocalSpeechRecordingStore(temporary.newFolder(), elapsedMillis = clock)
        return store to store.saveCapture(wav(), "r1", "session1", "speaker1")
    }

    private fun proof(capture: LocalSpeechRecording): JSONObject = JSONObject()
        .put("protocol", "android-local-audio-removal-v1").put("durableCopyVerified", true)
        .put("recordingId", capture.recordingId).put("speakerId", capture.speakerId)
        .put("sha256", capture.sha256).put("bytes", capture.bytes)
        .put("source", "android").put("requestNonce", nonce).put("copiesVerified", 1)

    @Test fun successfulRemovalPreservesEveryExistingMetadataLabelAndAnalysisFile() {
        val (store, capture) = fixture()
        store.saveStudentName(capture, "Test label")
        store.saveAnalysis(capture, "{\"observation\":\"test-only\"}")
        val folder = capture.audioFile.parentFile!!
        val history = folder.listFiles()!!.filter { it != capture.audioFile }.associateWith { it.readBytes().toList() }
        store.removeVerifiedLocalAudio(capture, proof(capture).toString(), nonce, 1000, true) { true }
        assertFalse(capture.audioFile.exists())
        for ((file, bytes) in history) assertEquals(bytes, file.readBytes().toList())
        assertEquals(1, folder.listFiles()!!.count { it.name.startsWith("local_audio_removal_request_") })
        assertEquals(1, folder.listFiles()!!.count { it.name.startsWith("local_audio_removal_completed_") })
    }

    @Test fun caregiverRefusalLeavesOriginalAndMetadataUntouched() {
        val (store, capture) = fixture()
        assertThrows(IllegalArgumentException::class.java) {
            store.removeVerifiedLocalAudio(capture, proof(capture).toString(), nonce, 1000, false) { true }
        }
        assertArrayEquals(wav(), capture.audioFile.readBytes())
        assertEquals(2, capture.audioFile.parentFile!!.listFiles()!!.size)
    }

    @Test fun transportReceiptCannotRemoveOriginal() {
        val (store, capture) = fixture()
        val receipt = proof(capture).put("protocol", "transport").put("durableCopyVerified", false)
        assertThrows(IllegalArgumentException::class.java) {
            store.removeVerifiedLocalAudio(capture, receipt.toString(), nonce, 1000, true) { true }
        }
        assertTrue(capture.audioFile.exists())
    }

    @Test fun corruptedLocalAudioCannotBeRemovedEvenWithMatchingOldPcReceipt() {
        val (store, capture) = fixture()
        capture.audioFile.writeBytes(byteArrayOf(1, 2, 3))
        assertThrows(java.io.IOException::class.java) {
            store.removeVerifiedLocalAudio(capture, proof(capture).toString(), nonce, 1000, true) { true }
        }
        assertArrayEquals(byteArrayOf(1, 2, 3), capture.audioFile.readBytes())
    }

    @Test fun proofExpiringDuringLocalVerificationLeavesAudioIntact() {
        var calls = 0
        val (store, capture) = fixture { if (calls++ == 0) 1000L else 32_001L }
        assertThrows(IllegalArgumentException::class.java) {
            store.removeVerifiedLocalAudio(capture, proof(capture).toString(), nonce, 1000, true) { true }
        }
        assertTrue(capture.audioFile.exists())
    }

    @Test fun changingPcSelectionBeforeRemovalLeavesAudioIntact() {
        val (store, capture) = fixture()
        assertThrows(java.io.IOException::class.java) {
            store.removeVerifiedLocalAudio(capture, proof(capture).toString(), nonce, 1000, true) { false }
        }
        assertTrue(capture.audioFile.exists())
    }

    @Test fun unexpectedFilePathCannotDeleteMetadata() {
        val (store, capture) = fixture()
        val meta = File(capture.audioFile.parentFile, "recording_meta.json")
        assertThrows(java.io.IOException::class.java) {
            store.removeVerifiedLocalAudio(capture.copy(audioFile = meta), proof(capture).toString(), nonce, 1000, true) { true }
        }
        assertTrue(meta.exists())
        assertTrue(capture.audioFile.exists())
    }
}
