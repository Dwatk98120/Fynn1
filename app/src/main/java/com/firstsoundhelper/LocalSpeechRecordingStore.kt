package com.firstsoundhelper

import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID

/**
 * The phone keeps an original completed capture before any attempt to upload it.
 * This is separate from the Windows Parent PC's permanent observation evidence.
 */
internal data class LocalSpeechRecording(
    val recordingId: String,
    val sessionId: String,
    val speakerId: String,
    val audioFile: File,
    val bytes: Long,
    val sha256: String
)

internal class LocalSpeechRecordingStore(filesDir: File) {
    private val history = File(filesDir, "dialogue_history")
    private val safeId = Regex("^[A-Za-z0-9_-]{1,100}$")

    private fun digest(audio: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(audio).joinToString("") { "%02x".format(it) }

    private fun isWav(audio: ByteArray): Boolean =
        audio.size >= 44 &&
            audio.copyOfRange(0, 4).contentEquals("RIFF".toByteArray(Charsets.US_ASCII)) &&
            audio.copyOfRange(8, 12).contentEquals("WAVE".toByteArray(Charsets.US_ASCII))

    private fun atomicCreate(target: File, payload: ByteArray) {
        if (target.exists()) throw IOException("Cannot overwrite existing recording evidence")
        val stage = File(target.parentFile, ".${target.name}.${UUID.randomUUID()}.tmp")
        try {
            FileOutputStream(stage).use { stream ->
                stream.write(payload)
                stream.fd.sync()
            }
            if (target.exists() || !stage.renameTo(target)) {
                throw IOException("Could not commit saved recording file")
            }
        } finally {
            if (stage.exists()) stage.delete()
        }
    }

    fun saveCapture(wav: ByteArray, recordingId: String, sessionId: String,
                    speakerId: String): LocalSpeechRecording {
        if (!isWav(wav)) throw IOException("Cannot save invalid WAV capture")
        if (!safeId.matches(recordingId) || !safeId.matches(sessionId) ||
            !safeId.matches(speakerId)) throw IOException("Invalid recording identity")
        if (!history.exists() && !history.mkdirs()) {
            throw IOException("Could not create local recording library")
        }
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(Date())
        val folder = File(history, "${timestamp}_${recordingId}")
        if (!folder.mkdir()) throw IOException("Could not create recording folder")
        val audioFile = File(folder, "recording.wav")
        val hash = digest(wav)
        atomicCreate(audioFile, wav)
        val metadata = JSONObject()
            .put("recordingId", recordingId)
            .put("sessionId", sessionId)
            .put("speakerId", speakerId)
            .put("bytes", wav.size.toLong())
            .put("sha256", hash)
            .put("capturedAtMillis", System.currentTimeMillis())
        atomicCreate(File(folder, "recording_meta.json"),
            metadata.toString(2).toByteArray(Charsets.UTF_8))
        return LocalSpeechRecording(recordingId, sessionId, speakerId,
            audioFile, wav.size.toLong(), hash)
    }

    /** Reject damaged or altered local recordings; never silently repair audio. */
    fun openSession(folder: File): LocalSpeechRecording? {
        try {
            if (folder.parentFile?.canonicalFile != history.canonicalFile) return null
            val audioFile = File(folder, "recording.wav")
            val metadataFile = File(folder, "recording_meta.json")
            if (!audioFile.isFile || !metadataFile.isFile) return null
            val metadata = JSONObject(metadataFile.readText(Charsets.UTF_8))
            val id = metadata.optString("recordingId")
            val session = metadata.optString("sessionId")
            val speaker = metadata.optString("speakerId")
            val hash = metadata.optString("sha256")
            val length = metadata.optLong("bytes", -1)
            if (!safeId.matches(id) || !safeId.matches(session) ||
                !safeId.matches(speaker) || !hash.matches(Regex("^[a-f0-9]{64}$")) ||
                length <= 44) return null
            val audio = audioFile.readBytes()
            if (!isWav(audio) || audio.size.toLong() != length || digest(audio) != hash) {
                return null
            }
            return LocalSpeechRecording(id, session, speaker, audioFile, length, hash)
        } catch (_: Exception) {
            return null
        }
    }

    fun latestVerified(): LocalSpeechRecording? {
        // Do not silently substitute an older recording if the newest is damaged.
        val newest = history.listFiles()
            ?.filter { it.isDirectory && File(it, "recording_meta.json").isFile }
            ?.maxByOrNull { it.name } ?: return null
        return openSession(newest)
    }

    fun verifiedWav(recording: LocalSpeechRecording): ByteArray {
        val reopened = openSession(recording.audioFile.parentFile
            ?: throw IOException("Recording folder missing"))
        if (reopened == null || reopened.recordingId != recording.recordingId ||
            reopened.sha256 != recording.sha256 ||
            reopened.speakerId != recording.speakerId ||
            reopened.sessionId != recording.sessionId) {
            throw IOException("Saved recording failed integrity verification")
        }
        return reopened.audioFile.readBytes().also {
            if (it.size.toLong() != reopened.bytes || digest(it) != reopened.sha256) {
                throw IOException("Saved audio changed during verification")
            }
        }
    }

    /**
     * Child names are caregiver-entered labels for THIS recording only.
     * They never rewrite the original WAV/identity metadata or change speaker ID.
     * Immutable events allow corrections without losing the previous label.
     */
    fun studentNameForRecording(recording: LocalSpeechRecording): String {
        verifiedWav(recording)
        val folder = recording.audioFile.parentFile ?: return ""
        val events = folder.listFiles()
            ?.filter { it.isFile && it.name.startsWith("student_label_") && it.name.endsWith(".json") }
            ?.sortedByDescending { it.name } ?: return ""
        for (event in events) {
            try {
                val label = JSONObject(event.readText(Charsets.UTF_8))
                if (label.optString("recordingId") != recording.recordingId ||
                    label.optString("audioSha256") != recording.sha256 ||
                    label.optString("speakerId") != recording.speakerId ||
                    label.optString("source") != "caregiver_on_android") continue
                val name = label.optString("studentName").trim()
                if (name.length <= 120 && name.none { it.code < 32 || it.code == 127 }) {
                    return name
                }
            } catch (_: Exception) {
                // An incomplete label event must never invalidate original audio.
            }
        }
        return ""
    }

    fun saveStudentName(recording: LocalSpeechRecording, studentName: String) {
        val name = studentName.trim()
        if (name.length > 120 || name.any { it.code < 32 || it.code == 127 }) {
            throw IOException("Child name must be 120 characters or less, without control characters")
        }
        if (studentNameForRecording(recording) == name) return
        val folder = recording.audioFile.parentFile ?: throw IOException("Recording folder missing")
        val event = JSONObject()
            .put("recordingId", recording.recordingId)
            .put("speakerId", recording.speakerId)
            .put("audioSha256", recording.sha256)
            .put("studentName", name)
            .put("source", "caregiver_on_android")
            .put("labeledAtMillis", System.currentTimeMillis())
        // Zero-padded sequence guarantees correction order even if two labels
        // happen to be entered within the same clock millisecond.
        val revision = (folder.listFiles()
            ?.count { it.name.startsWith("student_label_") && it.name.endsWith(".json") }
            ?: 0) + 1
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(Date())
        val sequence = String.format(Locale.US, "%012d", revision)
        atomicCreate(File(folder, "student_label_${sequence}_${stamp}_${UUID.randomUUID()}.json"),
            event.toString(2).toByteArray(Charsets.UTF_8))
    }

    /** Multiple analyses can be attached; the original recording never changes. */
    fun saveAnalysis(recording: LocalSpeechRecording, json: String) {
        verifiedWav(recording)
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(Date())
        atomicCreate(File(recording.audioFile.parentFile,
            "analysis_${stamp}_${UUID.randomUUID().toString().take(8)}.json"),
            json.toByteArray(Charsets.UTF_8))
    }
}

