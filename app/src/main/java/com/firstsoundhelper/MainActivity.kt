package com.firstsoundhelper
import android.widget.EditText
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.media.AudioManager
import java.util.concurrent.Executors

import android.Manifest
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.*
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.TimeUnit
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID
import android.media.MediaPlayer
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Button
import android.view.ViewGroup
import android.graphics.Color
import android.speech.tts.TextToSpeech
import android.speech.tts.TextToSpeech.OnInitListener
import org.json.JSONObject
import org.json.JSONArray
import kotlin.math.max
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.MediaStore
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.pdf.PdfDocument
import java.io.FileOutputStream

class MainActivity : AppCompatActivity() {
    private var tts: TextToSpeech? = null

    private lateinit var status: TextView
    private lateinit var result: TextView

    private var recorder: AudioRecord? = null
    private var recordingThread: Thread? = null
    private var recording = false
    private val pcm = ByteArrayOutputStream()
    private val sampleRate = 16000
    private fun parentPcApiBase(): String =
        getSharedPreferences("first_sound_helper_connection", MODE_PRIVATE)
            .getString("parent_pc_url", "")?.trim()?.trimEnd('/') ?: ""

    private fun normalizeParentPcUrl(raw: String): String {
        var v = raw.trim().trimEnd('/')
        if (v.isBlank()) return ""
        if (!v.startsWith("http://") && !v.startsWith("https://")) v = "http://$v"
        val hostPart = v.substringAfter("://")
        if (!hostPart.contains(":")) v += ":8000"
        return v
    }
    private val sentenceBuilderWords = mutableListOf<String>()
    // One ID for this app session; one new ID for every recording.
    // Both are created on the Android device before audio leaves the device.
    private val currentSessionId: String = UUID.randomUUID().toString()
    private var currentRecordingId: String = ""
    private var latestObservationId: String = ""
    private var latestRecordingId: String = ""
    private var wordBankDialog: android.app.Dialog? = null
    private var wordBankRecorder: MediaRecorder? = null
    private var wordBankRecordingFile: File? = null
    private val studentWordBank = linkedMapOf<String, File>()
    private var correctedSentenceTts: TextToSpeech? = null
    private var correctedSentenceReady = false
    private fun speakerId(): String {
        val p = getSharedPreferences("first_sound_helper_learning", MODE_PRIVATE)
        val existing = p.getString("speaker_id", "") ?: ""
        if (existing.isNotBlank()) return existing
        val created = UUID.randomUUID().toString()
        p.edit().putString("speaker_id", created).apply()
        return created
    }

    private val permission = registerForActivityResult(ActivityResultContracts.RequestPermission()) {
        if (it) startRecording() else status.text = "Microphone permission denied."
    }

    override fun onCreate(b: Bundle?) {
        super.onCreate(b); setContentView(R.layout.activity_main)
        

        // Live Speech
        val liveSpeechButton = android.widget.Button(this@MainActivity).apply {
            text = "Live Speech"
            setOnClickListener { startLiveSpeechMode() }
        }
        val phraseLibraryButton = Button(this@MainActivity)
        phraseLibraryButton.text = "Phrase Library"
        phraseLibraryButton.setOnClickListener { showPhraseLibrary() }
        val rootView = findViewById<ViewGroup>(android.R.id.content)
        findViewById<Button>(R.id.parentPcConnectionButton).setOnClickListener { showParentPcConnectionDialog() }
status=findViewById(R.id.status); result=findViewById(R.id.result); findViewById<Button>(R.id.recordButton).setOnClickListener {
            if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED)
                permission.launch(Manifest.permission.RECORD_AUDIO) else startRecording()
        }
        findViewById<Button>(R.id.stopButton).setOnClickListener { stopRecording() }
        findViewById<Button>(R.id.analyzeButton).setOnClickListener { showAnalyzeContextDialog() }
        findViewById<Button>(R.id.savedRecordingsButton).setOnClickListener { showSavedRecordings() }
        findViewById<Button>(R.id.liveRecordingButton).setOnClickListener { startLiveSpeechMode() }
        findViewById<Button>(R.id.studentToolsButton).setOnClickListener { showStudentCommunicationTools() }
        findViewById<Button>(R.id.communicationDictionaryButton).setOnClickListener { showCommunicationInterpretationTools() }
        findViewById<Button>(R.id.pilotReadinessButton).setOnClickListener { showCaregiverSetupAndReadiness() }
    }

    private fun startRecording() {
        val min=AudioRecord.getMinBufferSize(sampleRate,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT)
        recorder=AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION,sampleRate,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT,maxOf(min,sampleRate))
        currentRecordingId = UUID.randomUUID().toString()
        pcm.reset(); recording=true
        findViewById<Button>(R.id.recordButton).isEnabled=false
        findViewById<Button>(R.id.stopButton).isEnabled=true
        status.text="Listening…"
        recorder!!.startRecording()
        recordingThread=Thread {
            val buf=ByteArray(maxOf(min,4096))
            while(recording) { val n=recorder!!.read(buf,0,buf.size); if(n>0) synchronized(pcm){pcm.write(buf,0,n)} }
        }.also{it.start()}
    }

    private fun stopRecording() {
        recording=false
        try{recorder?.stop()}catch(_:Exception){}
        recorder?.release(); recorder=null
        findViewById<Button>(R.id.recordButton).isEnabled=true
        findViewById<Button>(R.id.stopButton).isEnabled=false
        status.text="Recording ready. Tap Analyze speech."
    }

    private fun wavBytes(): ByteArray {
        val audio=pcm.toByteArray(); val out=ByteArrayOutputStream()
        fun le(v:Int){out.write(byteArrayOf((v and 255).toByte(),((v shr 8) and 255).toByte(),((v shr 16) and 255).toByte(),((v shr 24) and 255).toByte()))}
        out.write("RIFF".toByteArray()); le(36+audio.size); out.write("WAVEfmt ".toByteArray()); le(16)
        out.write(byteArrayOf(1,0,1,0)); le(sampleRate); le(sampleRate*2); out.write(byteArrayOf(2,0,16,0))
        out.write("data".toByteArray()); le(audio.size); out.write(audio); return out.toByteArray()
    }



    private fun popupDp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()

    private fun popupBackground(color: String, radiusDp: Int = 24): android.graphics.drawable.GradientDrawable =
        android.graphics.drawable.GradientDrawable().apply {
            setColor(android.graphics.Color.parseColor(color))
            cornerRadius = popupDp(radiusDp).toFloat()
        }

    private fun styleUnifiedDialog(dialog: android.app.Dialog) {
        dialog.window?.let { w ->
            w.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT))
            w.addFlags(android.view.WindowManager.LayoutParams.FLAG_DIM_BEHIND)
            val lp = w.attributes
            lp.dimAmount = 0.48f
            w.attributes = lp
            w.decorView.post {
                val width = (resources.displayMetrics.widthPixels * 0.91f).toInt()
                w.setLayout(width, android.view.ViewGroup.LayoutParams.WRAP_CONTENT)
                w.decorView.background = popupBackground("#FFFFFF", 26)
                w.decorView.setPadding(popupDp(2), popupDp(2), popupDp(2), popupDp(2))
            }
        }

        val alertTitleId = resources.getIdentifier("alertTitle", "id", "android")
        if (alertTitleId != 0) {
            dialog.findViewById<android.widget.TextView?>(alertTitleId)?.apply {
                setTextColor(android.graphics.Color.parseColor("#21124D"))
                textSize = 22f
                setTypeface(typeface, android.graphics.Typeface.BOLD)
            }
        }
        dialog.findViewById<android.widget.TextView?>(android.R.id.message)?.apply {
            setTextColor(android.graphics.Color.parseColor("#4B4855"))
            textSize = 16f
            setLineSpacing(0f, 1.12f)
        }
        dialog.findViewById<android.widget.Button?>(android.R.id.button1)?.apply {
            setTextColor(android.graphics.Color.parseColor("#6D4DB3"))
            isAllCaps = false
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        dialog.findViewById<android.widget.Button?>(android.R.id.button2)?.apply {
            setTextColor(android.graphics.Color.parseColor("#5C5965"))
            isAllCaps = false
        }
        dialog.findViewById<android.widget.Button?>(android.R.id.button3)?.apply {
            setTextColor(android.graphics.Color.parseColor("#6D4DB3"))
            isAllCaps = false
        }

        dialog.window?.decorView?.post {
            stylePopupTree(dialog.window?.decorView)
            dialog.findViewById<android.widget.Button?>(android.R.id.button1)?.apply {
                setTextColor(android.graphics.Color.parseColor("#FFFFFF"))
                background = popupBackground("#6D4DB3", 16)
                setTypeface(typeface, android.graphics.Typeface.BOLD)
            }
            dialog.findViewById<android.widget.Button?>(android.R.id.button2)?.apply {
                setTextColor(android.graphics.Color.parseColor("#5C5965"))
                background = popupBackground("#F3F1F6", 16)
            }
            dialog.findViewById<android.widget.Button?>(android.R.id.button3)?.apply {
                setTextColor(android.graphics.Color.parseColor("#4D27A6"))
                background = popupBackground("#F1ECFC", 16)
            }
        }
    }


    private fun stylePopupTree(view: android.view.View?) {
        if (view == null) return

        when (view) {
            is android.widget.Button -> {
                view.isAllCaps = false
                view.textSize = 15f
                view.minHeight = popupDp(54)
                view.setPadding(popupDp(16), popupDp(9), popupDp(14), popupDp(9))
                view.setTextColor(android.graphics.Color.parseColor("#4D27A6"))
                view.background = popupBackground("#F1ECFC", 18)
                view.setTypeface(view.typeface, android.graphics.Typeface.BOLD)
            }

            is android.widget.EditText -> {
                view.textSize = 16f
                view.setTextColor(android.graphics.Color.parseColor("#3F3B48"))
                view.setHintTextColor(android.graphics.Color.parseColor("#88838F"))
                view.background = popupBackground("#F7F4FD", 14)
                view.setPadding(popupDp(14), popupDp(11), popupDp(14), popupDp(11))
            }

            is android.widget.TextView -> {
                if (view.textSize >= 20f) {
                    view.setTextColor(android.graphics.Color.parseColor("#21124D"))
                    view.setTypeface(view.typeface, android.graphics.Typeface.BOLD)
                } else {
                    view.setTextColor(android.graphics.Color.parseColor("#53505D"))
                    view.setLineSpacing(0f, 1.08f)
                }
            }
        }

        if (view is android.view.ViewGroup) {
            for (i in 0 until view.childCount) {
                stylePopupTree(view.getChildAt(i))
            }
        }
    }

    private fun popupHeader(title: String, subtitle: String? = null, icon: String = "✨"): android.widget.LinearLayout =
        android.widget.LinearLayout(this@MainActivity).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(popupDp(8), popupDp(4), popupDp(8), popupDp(12))

            addView(android.widget.TextView(this@MainActivity).apply {
                text = "$icon  $title"
                textSize = 24f
                setTextColor(android.graphics.Color.parseColor("#21124D"))
                setTypeface(typeface, android.graphics.Typeface.BOLD)
            })

            if (!subtitle.isNullOrBlank()) {
                addView(android.widget.TextView(this@MainActivity).apply {
                    text = subtitle
                    textSize = 15f
                    setTextColor(android.graphics.Color.parseColor("#666270"))
                    setPadding(0, popupDp(6), 0, 0)
                })
            }
        }

    private fun popupActionButton(
        title: String,
        description: String? = null,
        icon: String = "›",
        primary: Boolean = false,
        action: () -> Unit
    ): android.widget.Button =
        android.widget.Button(this@MainActivity).apply {
            text = buildString {
                append(icon)
                append("  ")
                append(title)
                if (!description.isNullOrBlank()) {
                    append("\n")
                    append(description)
                }
                append("   ›")
            }
            textSize = if (description.isNullOrBlank()) 16f else 15f
            isAllCaps = false
            gravity = android.view.Gravity.START or android.view.Gravity.CENTER_VERTICAL
            minHeight = popupDp(if (description.isNullOrBlank()) 58 else 70)
            setPadding(popupDp(18), popupDp(10), popupDp(14), popupDp(10))
            setTextColor(android.graphics.Color.parseColor(if (primary) "#FFFFFF" else "#4D27A6"))
            background = popupBackground(if (primary) "#6D4DB3" else "#F1ECFC", 18)
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            val lp = android.widget.LinearLayout.LayoutParams(
                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                android.view.ViewGroup.LayoutParams.WRAP_CONTENT
            )
            lp.setMargins(0, popupDp(5), 0, popupDp(5))
            layoutParams = lp
            setOnClickListener { action() }
        }

    private fun popupInfoCard(title: String, body: String, icon: String = "✓"): android.widget.LinearLayout =
        android.widget.LinearLayout(this@MainActivity).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(popupDp(16), popupDp(14), popupDp(16), popupDp(14))
            background = popupBackground("#F7F4FD", 18)

            addView(android.widget.TextView(this@MainActivity).apply {
                text = "$icon  $title"
                textSize = 17f
                setTextColor(android.graphics.Color.parseColor("#40218F"))
                setTypeface(typeface, android.graphics.Typeface.BOLD)
            })
            addView(android.widget.TextView(this@MainActivity).apply {
                text = body
                textSize = 15f
                setTextColor(android.graphics.Color.parseColor("#53505D"))
                setPadding(0, popupDp(8), 0, 0)
                setLineSpacing(0f, 1.1f)
            })
        }

    private fun showAnalyzeContextDialog() {
        val box = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 24, 40, 8)
        }

        val prompt = TextView(this@MainActivity).apply {
            text = "Optional context"
            textSize = 18f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

        val helper = TextView(this@MainActivity).apply {
            text = "Add a short clue if it may help the analysis. You can leave this blank."
            textSize = 14f
            setPadding(0, 8, 0, 10)
        }

        val input = EditText(this@MainActivity).apply {
            hint = "Example: I see a ___"
            setText(pendingAnalyzeContext)
            isSingleLine = true
        }

        box.addView(prompt)
        box.addView(helper)
        box.addView(input)

        val dialog = androidx.appcompat.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Analyze Speech")
            .setView(box)
            .setPositiveButton("Analyze") { _, _ ->
                pendingAnalyzeContext = input.text.toString().trim()
                uploadForAnalysis()
            }
            .setNegativeButton("Cancel", null)
            .create()
        dialog.setOnShowListener { styleUnifiedDialog(dialog) }
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun uploadForAnalysis() {
        val base = parentPcApiBase()
        if (base.isBlank()) {
            status.text = "Parent PC not configured"
            result.text = "Parent PC is required for analysis. Tap Parent PC Connection and enter or discover your Parent PC."
            return
        }
        if (getPreferences(MODE_PRIVATE).getBoolean("offline_mode", false)) {
            status.text = "Offline mode is on"
            result.text = "Analysis upload is disabled. You can still use sentence building, word bank, phrases, choices, and playback."
            return
        }
        if(pcm.size()==0){result.text="Record a short word or phrase first.";return}
        status.text="Analyzing phonemes…"; result.text="Listening for initial and final consonant patterns and comparing possible words…"
        Thread {
            try {
                val client=OkHttpClient.Builder().connectTimeout(20,TimeUnit.SECONDS).readTimeout(120,TimeUnit.SECONDS).build()
                val body=MultipartBody.Builder().setType(MultipartBody.FORM)
                    .addFormDataPart("context",pendingAnalyzeContext)
                    .addFormDataPart("session_id", currentSessionId)
                    .addFormDataPart("recording_id", currentRecordingId.ifBlank { UUID.randomUUID().toString().also { currentRecordingId = it } })
                    .addFormDataPart("speaker_id", speakerId())
                    .addFormDataPart("audio","speech.wav",wavBytes().toRequestBody("audio/wav".toMediaType()))
                    .build()
                val req=Request.Builder().url("$base/v1/analyze-audio").post(body).build()
                client.newCall(req).execute().use { r ->
                    val txt=r.body?.string()?:""
                    runOnUiThread {
                        if (r.isSuccessful) {
                            status.text = "Analysis complete"
                            result.text = formatAnalysisResult(txt)
                        } else {
                            status.text = "Parent PC analysis failed"
                            result.text = if (txt.trimStart().startsWith("<")) {
                                "The Parent PC server returned an unexpected web page instead of analysis data."
                            } else {
                                "Parent PC error ${r.code}: " + txt.take(500)
                            }
                        }
                    }
                }
            } catch(e:Exception) { runOnUiThread { status.text="Could not reach analysis server"; result.text=e.message ?: "Network error" } }
        }.start()
    }


    private fun sendLearningFeedback(word: String, approvedForLearning: Boolean) {
        val observationId = latestObservationId
        val base = parentPcApiBase()
        if (observationId.isBlank() || word.isBlank() || base.isBlank()) return
        Thread {
            try {
                val client = OkHttpClient.Builder()
                    .connectTimeout(20, TimeUnit.SECONDS)
                    .readTimeout(60, TimeUnit.SECONDS)
                    .build()
                val body = MultipartBody.Builder().setType(MultipartBody.FORM)
                    .addFormDataPart("observation_id", observationId)
                    .addFormDataPart("recording_id", latestRecordingId)
                    .addFormDataPart("speaker_id", speakerId())
                    .addFormDataPart("confirmed_word", word)
                    .addFormDataPart("approved_for_learning", approvedForLearning.toString())
                    .build()
                val req = Request.Builder().url("$base/v1/learning/feedback").post(body).build()
                client.newCall(req).execute().use { response ->
                    if (!response.isSuccessful) {
                        runOnUiThread {
                            android.widget.Toast.makeText(
                                this,
                                "Feedback saved locally in the app, but server learning was not updated.",
                                android.widget.Toast.LENGTH_LONG
                            ).show()
                        }
                    }
                }
            } catch (_: Exception) {
                // Learning feedback should never prevent normal communication use.
            }
        }.start()
    }


    private fun showParentPcConnectionDialog() {
        val content = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(popupDp(22), popupDp(18), popupDp(22), popupDp(10))
        }

        content.addView(popupHeader(
            "Parent PC Connection",
            "Connect this phone to the Parent PC for local speech analysis and learning.",
            "🖥️"
        ))

        content.addView(popupInfoCard(
            "Local connection",
            "Enter the Parent PC address shown by the local server. Both devices should be on the same local network.",
            "🟢"
        ).apply {
            val lp = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            lp.setMargins(0, popupDp(5), 0, popupDp(12))
            layoutParams = lp
        })

        val label = TextView(this@MainActivity).apply {
            text = "Parent PC address"
            textSize = 15f
            setTextColor(android.graphics.Color.parseColor("#32245C"))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setPadding(0, popupDp(4), 0, popupDp(5))
        }
        content.addView(label)

        val input = EditText(this@MainActivity).apply {
            hint = "Example: 192.168.1.25:8000"
            setText(parentPcApiBase())
            isSingleLine = true
            background = popupBackground("#F7F4FD", 14)
            setPadding(popupDp(14), popupDp(12), popupDp(14), popupDp(12))
        }
        content.addView(input)

        content.addView(popupActionButton(
            "Test Connection",
            "Check whether the Parent PC service can be reached.",
            "⚙️"
        ) {
            val url = normalizeParentPcUrl(input.text.toString())
            if (url.isBlank()) {
                Toast.makeText(this@MainActivity, "Enter the Parent PC address first.", Toast.LENGTH_SHORT).show()
            } else {
                testParentPcConnection(url)
            }
        })

        val dialog = android.app.Dialog(this@MainActivity)
        content.addView(popupActionButton("Save Connection", null, "✓", true) {
            val url = normalizeParentPcUrl(input.text.toString())
            getSharedPreferences("first_sound_helper_connection", MODE_PRIVATE)
                .edit().putString("parent_pc_url", url).apply()
            status.text = if (url.isBlank()) "Parent PC not configured" else "Parent PC saved: $url"
            dialog.dismiss()
        })
        content.addView(popupActionButton("Cancel", null, "×") { dialog.dismiss() })

        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(content) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun testParentPcConnection(base: String) {
        status.text = "Testing Parent PC…"
        Thread {
            try {
                val client = OkHttpClient.Builder()
                    .connectTimeout(5, TimeUnit.SECONDS)
                    .readTimeout(10, TimeUnit.SECONDS)
                    .build()
                val req = Request.Builder().url("$base/health").get().build()
                client.newCall(req).execute().use { response ->
                    val ok = response.isSuccessful
                    runOnUiThread {
                        status.text = if (ok) "Parent PC connected" else "Parent PC responded with ${response.code}"
                        Toast.makeText(
                            this@MainActivity,
                            if (ok) "Parent PC connection successful." else "Parent PC connection failed.",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    status.text = "Could not reach Parent PC"
                    Toast.makeText(
                        this@MainActivity,
                        "Could not reach Parent PC: ${e.message ?: "network error"}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }.start()
    }

    override fun onDestroy(){ recording=false; try{recorder?.release()}catch(_:Exception){}; super.onDestroy() }

    private fun formatAnalysisResult(json: String): String {
        return try {
            val obj = JSONObject(json)
            val transcript = obj.optString("transcript", "").ifBlank { "—" }
            val recordingId = obj.optString("recordingId", "")
            val observation = obj.optJSONObject("observation")
            val observationId = observation?.optString("observationId", "") ?: ""
            latestRecordingId = recordingId
            latestObservationId = observationId
            val analysis = obj.optJSONObject("analysis")
            val candidates = obj.optJSONArray("candidates")
            val lines = mutableListOf<String>()
            lines += "Heard: $transcript"
            if (recordingId.isNotBlank()) lines += "Recording ID: $recordingId"
            if (observationId.isNotBlank()) lines += "Observation ID: $observationId"
            val overall = analysis?.optDouble("overallConfidence", -1.0) ?: -1.0
            val uncertainty = analysis?.optString("uncertaintyBand", "") ?: ""
            if (overall >= 0.0) {
                lines += "AI candidate confidence: ${String.format(Locale.US, "%.2f", overall)}" +
                    if (uncertainty.isNotBlank()) " ($uncertainty uncertainty)" else ""
            }
            if (analysis?.optBoolean("possibleInitialConsonantOmission", false) == true) {
                lines += "Possible initial-consonant deletion detected."
            }
            if (analysis?.optBoolean("possibleFinalConsonantOmission", false) == true) {
                lines += "Possible final-consonant deletion detected."
            }
            if ((analysis?.optBoolean("possibleInitialConsonantOmission", false) != true) &&
                (analysis?.optBoolean("possibleFinalConsonantOmission", false) != true)) {
                lines += "No initial- or final-consonant deletion pattern was identified in the candidate set."
            }
            if (candidates != null && candidates.length() > 0) {
                lines += ""
                lines += "Possible words:"
                for (i in 0 until minOf(candidates.length(), 8)) {
                    val c = candidates.getJSONObject(i)
                    val word = c.optString("word", "")
                    val pattern = c.optString("pattern", "possible sound pattern")
                    val missing = if (c.optBoolean("possibleFinalOmission", false)) c.optString("missingFinal", "") else c.optString("missingInitial", "")
                    val soundText = if (missing.isNotBlank()) " (missing $missing)" else ""
                    val conf = c.optDouble("confidence", -1.0)
                    val confText = if (conf >= 0.0) " • confidence ${String.format(Locale.US, "%.2f", conf)}" else ""
                    lines += "• $word — $pattern$soundText$confText"
                }
            }
            lines += ""
            lines += "These are probabilistic speech observations, not a clinical diagnosis."
            lines.joinToString("\n")
        } catch (_: Exception) {
            json
        }
    }

    private fun saveDialogueRecord(wavFile: File, resultJson: String) {
        val dir = File(filesDir, "dialogue_history")
        if (!dir.exists()) dir.mkdirs()
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(Date())
        val sessionDir = File(dir, stamp)
        sessionDir.mkdirs()
        File(sessionDir, "recording.wav").writeBytes(wavFile.readBytes())
        File(sessionDir, "analysis.json").writeText(resultJson)
    }

    private fun deleteAllSavedDialogue() {
        val dir = File(filesDir, "dialogue_history")
        if (dir.exists()) dir.deleteRecursively()
    }

    private fun showSavedRecordings() {
        val dialog = android.app.Dialog(this@MainActivity)
        dialog.setTitle("Saved Recordings")

        val scroll = ScrollView(this@MainActivity)
        val list = LinearLayout(this@MainActivity)
        list.orientation = LinearLayout.VERTICAL
        list.setPadding(32, 24, 32, 24)
        scroll.addView(list)

        val dir = File(filesDir, "dialogue_history")
        val sessions = if (dir.exists()) {
            dir.listFiles()?.filter { it.isDirectory }?.sortedByDescending { it.name } ?: emptyList()
        } else emptyList()

        if (sessions.isEmpty()) {
            val empty = TextView(this@MainActivity)
            empty.text = "No saved recordings yet."
            empty.textSize = 18f
            list.addView(empty)
        } else {
            sessions.forEach { session ->
                val title = TextView(this@MainActivity)
                title.text = session.name
                title.textSize = 17f
                title.setPadding(0, 18, 0, 8)
                list.addView(title)

                val analysis = File(session, "analysis.json")
                val audio = File(session, "recording.wav")

                val row = LinearLayout(this@MainActivity)
                row.orientation = LinearLayout.HORIZONTAL

                val play = Button(this@MainActivity)
                play.text = "Play"
                play.setOnClickListener {
                    if (audio.exists()) {
                        val player = MediaPlayer()
                        player.setDataSource(audio.absolutePath)
                        player.prepare()
                        player.start()
                        player.setOnCompletionListener { it.release() }
                    }
                }

                val view = Button(this@MainActivity)
                view.text = "View"
                view.setOnClickListener {
                    val text = if (analysis.exists()) analysis.readText() else "No analysis saved."
                    android.app.AlertDialog.Builder(this@MainActivity)
                        .setTitle("Analysis — ${session.name}")
                        .setMessage(text)
                        .setPositiveButton("Close", null)
                        .show()
                }

                val delete = Button(this@MainActivity)
                delete.text = "Delete"
                delete.setOnClickListener {
                    android.app.AlertDialog.Builder(this@MainActivity)
                        .setTitle("Delete recording?")
                        .setMessage("This removes the saved audio and analysis from this device.")
                        .setNegativeButton("Cancel", null)
                        .setPositiveButton("Delete") { _, _ ->
                            session.deleteRecursively()
                            dialog.dismiss()
                            showSavedRecordings()
                        }
                        .show()
                }

                row.addView(play, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
                row.addView(view, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
                row.addView(delete, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
                list.addView(row)
            }

            val deleteAll = Button(this@MainActivity)
            deleteAll.text = "Delete All Saved Recordings"
            deleteAll.setOnClickListener {
                android.app.AlertDialog.Builder(this@MainActivity)
                    .setTitle("Delete all recordings?")
                    .setMessage("This cannot be undone.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Delete All") { _, _ ->
                        if (dir.exists()) dir.deleteRecursively()
                        dialog.dismiss()
                    }
                    .show()
            }
            list.addView(deleteAll)
        }

        dialog.setContentView(scroll)
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun speakSuggestedWord(word: String) {
        if (tts == null) {
            tts = TextToSpeech(this@MainActivity) { status ->
                if (status == TextToSpeech.SUCCESS) {
                    tts?.speak(word, TextToSpeech.QUEUE_FLUSH, null, "suggested_word")
                }
            }
        } else {
            tts?.speak(word, TextToSpeech.QUEUE_FLUSH, null, "suggested_word")
        }
    }

    private fun showSuggestedWords(words: List<Pair<String, String>>) {
        if (words.isEmpty()) return

        val dialog = android.app.Dialog(this@MainActivity)
        dialog.setTitle("Possible Words")

        val scroll = android.widget.ScrollView(this@MainActivity)
        val list = android.widget.LinearLayout(this@MainActivity)
        list.orientation = android.widget.LinearLayout.VERTICAL
        list.setPadding(28, 20, 28, 20)

        val intro = android.widget.TextView(this@MainActivity)
        intro.text = "Possible words based on the analyzed first sound. These are suggestions, not a diagnosis."
        intro.textSize = 16f
        list.addView(intro)

        words.forEach { pair ->
            val word = pair.first
            val missing = pair.second

            val row = android.widget.LinearLayout(this@MainActivity)
            row.orientation = android.widget.LinearLayout.VERTICAL
            row.setPadding(0, 18, 0, 18)

            val label = android.widget.TextView(this@MainActivity)
            label.text = "$word  —  possible missing first sound: $missing"
            label.textSize = 19f
            row.addView(label)

            val buttons = android.widget.LinearLayout(this@MainActivity)
            buttons.orientation = android.widget.LinearLayout.HORIZONTAL

            val play = android.widget.Button(this@MainActivity)
            play.text = "🔊 Play"
            play.setOnClickListener { speakSuggestedWord(word) }

            val confirm = android.widget.Button(this@MainActivity)
            confirm.text = "That's it"
            confirm.setOnClickListener {
                if (latestObservationId.isBlank()) {
                    android.widget.Toast.makeText(this@MainActivity, "Analyze a recording first.", android.widget.Toast.LENGTH_SHORT).show()
                } else {
                    sendLearningFeedback(word, approvedForLearning = true)
                    android.widget.Toast.makeText(
                        this,
                        "Confirmed and approved for learning: $word",
                        android.widget.Toast.LENGTH_SHORT
                    ).show()
                }
            }

            buttons.addView(play, android.widget.LinearLayout.LayoutParams(0, -2, 1f))
            buttons.addView(confirm, android.widget.LinearLayout.LayoutParams(0, -2, 1f))
            row.addView(buttons)
            list.addView(row)
        }

        scroll.addView(list)
        dialog.setContentView(scroll)
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun extractSuggestedWords(json: String): List<Pair<String, String>> {
        val results = mutableListOf<Pair<String, String>>()
        val candidateRegex = Regex(
            """\{\s*"word"\s*:\s*"([^"]+)".*?"missingInitial"\s*:\s*"([^"]*)".*?\}""",
            setOf(RegexOption.DOT_MATCHES_ALL)
        )
        candidateRegex.findAll(json).take(8).forEach { m ->
            val word=m.groupValues[1]
            val missing=m.groupValues[2]
            if (word.isNotBlank()) results.add(word to if (missing.isBlank()) "possible initial consonant" else missing)
        }
        return results
    }

    private fun phraseFile(): File = File(filesDir, "saved_phrases.json")

    private fun normalizePhrase(s: String): String {
        return s.lowercase(Locale.US)
            .replace(Regex("[^a-z0-9\\s']"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
    }

    private fun loadSavedPhrases(): MutableList<String> {
        val f = phraseFile()
        if (!f.exists()) return mutableListOf()
        return try {
            val arr = JSONArray(f.readText())
            MutableList(arr.length()) { i -> arr.getString(i) }
        } catch (_: Exception) {
            mutableListOf()
        }
    }

    private fun saveSavedPhrases(phrases: List<String>) {
        val arr = JSONArray()
        phrases.distinct().forEach { arr.put(it) }
        phraseFile().writeText(arr.toString())
    }

    private fun addSavedPhrase(phrase: String) {
        val p = phrase.trim()
        if (p.isBlank()) return
        val phrases = loadSavedPhrases()
        if (phrases.none { normalizePhrase(it) == normalizePhrase(p) }) {
            phrases.add(p)
            saveSavedPhrases(phrases)
        }
    }

    private fun phraseSimilarity(a: String, b: String): Double {
        val x = normalizePhrase(a)
        val y = normalizePhrase(b)
        if (x.isBlank() || y.isBlank()) return 0.0
        if (x == y) return 1.0
        val aa = x.split(" ").filter { it.isNotBlank() }.toSet()
        val bb = y.split(" ").filter { it.isNotBlank() }.toSet()
        val intersection = aa.intersect(bb).size.toDouble()
        val union = aa.union(bb).size.toDouble()
        val jaccard = if (union == 0.0) 0.0 else intersection / union

        fun levenshtein(s: String, t: String): Int {
            var prev = IntArray(t.length + 1) { it }
            for (i in s.indices) {
                val cur = IntArray(t.length + 1)
                cur[0] = i + 1
                for (j in t.indices) {
                    val cost = if (s[i] == t[j]) 0 else 1
                    cur[j + 1] = minOf(cur[j] + 1, prev[j + 1] + 1, prev[j] + cost)
                }
                prev = cur
            }
            return prev[t.length]
        }

        val maxLen = max(x.length, y.length).coerceAtLeast(1)
        val editScore = 1.0 - levenshtein(x, y).toDouble() / maxLen
        return max(jaccard, editScore * 0.85)
    }

    private fun extractRecognizedPhrase(json: String): String {
        return try {
            val obj = JSONObject(json)
            when {
                obj.has("recognizedPhrase") -> obj.optString("recognizedPhrase")
                obj.has("transcript") -> obj.optString("transcript")
                else -> ""
            }
        } catch (_: Exception) {
            ""
        }
    }

    private fun showPhraseMatchResult(recognized: String) {
        if (recognized.isBlank()) return
        val phrases = loadSavedPhrases()
        if (phrases.isEmpty()) return

        val ranked = phrases.map { it to phraseSimilarity(recognized, it) }
            .sortedByDescending { it.second }
        val best = ranked.firstOrNull() ?: return

        if (best.second >= 0.72) {
            val percent = (best.second * 100).toInt().coerceIn(0, 100)
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Possible matching phrase")
                .setMessage("Heard:\n$recognized\n\nSaved phrase:\n${best.first}\n\nMatch: $percent%")
                .setNegativeButton("Not the same", null)
                .setPositiveButton("That's the phrase") { _, _ ->
                    android.widget.Toast.makeText(this@MainActivity, "Phrase confirmed.", android.widget.Toast.LENGTH_SHORT).show()
                }
                .create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
        }
    }

    private fun showPhraseLibrary() {
        val dialog = android.app.Dialog(this@MainActivity)
        dialog.setTitle("Phrase Library")
        val scroll = android.widget.ScrollView(this@MainActivity)
        val list = android.widget.LinearLayout(this@MainActivity)
        list.orientation = android.widget.LinearLayout.VERTICAL
        list.setPadding(28, 20, 28, 20)

        val phrases = loadSavedPhrases()
        if (phrases.isEmpty()) {
            val empty = android.widget.TextView(this@MainActivity)
            empty.text = "No saved phrases yet."
            empty.textSize = 18f
            list.addView(empty)
        } else {
            phrases.forEach { phrase ->
                val row = android.widget.LinearLayout(this@MainActivity)
                row.orientation = android.widget.LinearLayout.HORIZONTAL
                val label = android.widget.TextView(this@MainActivity)
                label.text = phrase
                label.textSize = 18f
                label.setPadding(0, 14, 8, 14)
                row.addView(label, android.widget.LinearLayout.LayoutParams(0, -2, 1f))

                val play = android.widget.Button(this@MainActivity)
                play.text = "Play"
                play.setOnClickListener { speakSuggestedWord(phrase) }
                row.addView(play)

                val delete = android.widget.Button(this@MainActivity)
                delete.text = "Delete"
                delete.setOnClickListener {
                    val updated = loadSavedPhrases().filterNot { it == phrase }
                    saveSavedPhrases(updated)
                    dialog.dismiss()
                    showPhraseLibrary()
                }
                row.addView(delete)
                list.addView(row)
            }
        }

        val add = android.widget.Button(this@MainActivity)
        add.text = "Add Phrase"
        add.setOnClickListener {
            val input = android.widget.EditText(this@MainActivity)
            input.hint = "Type a phrase"
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Save a phrase")
                .setView(input)
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Save") { _, _ ->
                    addSavedPhrase(input.text.toString())
                    dialog.dismiss()
                    showPhraseLibrary()
                }.show()
        }
        list.addView(add)

        val clear = android.widget.Button(this@MainActivity)
        clear.text = "Delete All Phrases"
        clear.setOnClickListener {
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Delete phrase library?")
                .setMessage("This removes all saved phrases from this device.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Delete All") { _, _ ->
                    phraseFile().delete()
                    dialog.dismiss()
                }.show()
        }
        list.addView(clear)

        scroll.addView(list)
        dialog.setContentView(scroll)
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showConsonantPatterns() {
        val dir = File(filesDir, "dialogue_history")
        val sessions = if (dir.exists()) {
            dir.listFiles()?.filter { it.isDirectory } ?: emptyList()
        } else emptyList()

        val wordCounts = mutableMapOf<String, Int>()
        val soundCounts = mutableMapOf<String, Int>()

        sessions.forEach { session ->
            val f = File(session, "analysis.json")
            if (!f.exists()) return@forEach
            val json = f.readText()

            val candidateRegex = Regex(
                """\{\s*"word"\s*:\s*"([^"]+)".*?"missingInitial"\s*:\s*"([^"]*)".*?"missingFinal"\s*:\s*"([^"]*)".*?"possibleInitialOmission"\s*:\s*(true|false).*?"possibleFinalOmission"\s*:\s*(true|false).*?\}""",
                setOf(RegexOption.DOT_MATCHES_ALL)
            )
            candidateRegex.findAll(json).forEach { m ->
                val word=m.groupValues[1].trim()
                val initialSound=m.groupValues[2].trim()
                val finalSound=m.groupValues[3].trim()
                val initialOmission=m.groupValues[4].equals("true", ignoreCase=true)
                val finalOmission=m.groupValues[5].equals("true", ignoreCase=true)
                if ((initialOmission || finalOmission) && word.isNotBlank()) {
                    wordCounts[word] = (wordCounts[word] ?: 0) + 1
                    val sound = if (finalOmission) finalSound else initialSound
                    if (sound.isNotBlank()) soundCounts[sound] = (soundCounts[sound] ?: 0) + 1
                }
            }
        }

        val topWords = wordCounts.entries.sortedByDescending { it.value }.take(15)
        val topSounds = soundCounts.entries.sortedByDescending { it.value }.take(10)

        val scroll = android.widget.ScrollView(this@MainActivity)
        val list = android.widget.LinearLayout(this@MainActivity)
        list.orientation = android.widget.LinearLayout.VERTICAL
        list.setPadding(32,24,32,24)

        val title = android.widget.TextView(this@MainActivity)
        title.text = "Consonant Patterns"
        title.textSize = 24f
        list.addView(title)

        val note = android.widget.TextView(this@MainActivity)
        note.text = "This report summarizes possible initial- and final-consonant omissions found in saved recordings. It is a pattern summary, not a clinical assessment."
        note.textSize = 15f
        note.setPadding(0,12,0,24)
        list.addView(note)

        val soundTitle = android.widget.TextView(this@MainActivity)
        soundTitle.text = "Most frequent possible missing consonant sounds"
        soundTitle.textSize = 19f
        list.addView(soundTitle)

        if (topSounds.isEmpty()) {
            val empty = android.widget.TextView(this@MainActivity)
            empty.text = "No possible omissions have been recorded yet."
            empty.setPadding(0,12,0,24)
            list.addView(empty)
        } else {
            topSounds.forEachIndexed { i, e ->
                val row = android.widget.TextView(this@MainActivity)
                row.text = "${i+1}. ${e.key}  —  ${e.value} possible omission${if (e.value==1) "" else "s"}"
                row.textSize = 18f
                row.setPadding(0,8,0,8)
                list.addView(row)
            }
        }

        val wordTitle = android.widget.TextView(this@MainActivity)
        wordTitle.text = "Words with repeated possible omissions"
        wordTitle.textSize = 19f
        wordTitle.setPadding(0,24,0,8)
        list.addView(wordTitle)

        if (topWords.isEmpty()) {
            val empty = android.widget.TextView(this@MainActivity)
            empty.text = "No repeated words yet."
            list.addView(empty)
        } else {
            topWords.forEachIndexed { i, e ->
                val row = android.widget.TextView(this@MainActivity)
                row.text = "${i+1}. ${e.key}  —  ${e.value} time${if (e.value==1) "" else "s"}"
                row.textSize = 18f
                row.setPadding(0,8,0,8)
                list.addView(row)
            }
        }

        val clear = android.widget.Button(this@MainActivity)
        clear.text = "Close"
        clear.setOnClickListener { /* dialog closed below */ }
        list.addView(clear)

        val dialog = android.app.Dialog(this@MainActivity)
        clear.setOnClickListener { dialog.dismiss() }
        scroll.addView(list)
        dialog.setContentView(scroll)
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun studentDir(): File {
        val d = File(filesDir, "student_profile")
        if (!d.exists()) d.mkdirs()
        return d
    }

    private fun studentInfoFile(): File = File(studentDir(), "profile.json")
    private var pendingPhotoUri: Uri? = null

    private fun saveStudentProfile(name: String, studentId: String, notes: String) {
        val obj = JSONObject()
        obj.put("name", name)
        obj.put("studentId", studentId)
        obj.put("notes", notes)
        studentInfoFile().writeText(obj.toString())
    }

    private fun loadStudentProfile(): JSONObject {
        return try {
            if (studentInfoFile().exists()) JSONObject(studentInfoFile().readText())
            else JSONObject()
        } catch (_: Exception) { JSONObject() }
    }

    private fun showStudentProfile() {
        val p=loadStudentProfile()
        val box=android.widget.LinearLayout(this@MainActivity)
        box.orientation=android.widget.LinearLayout.VERTICAL
        box.setPadding(28,20,28,20)

        val photo=android.widget.ImageView(this)
        val photoFile=File(studentDir(),"student_photo.jpg")
        if (photoFile.exists()) {
            photo.setImageBitmap(BitmapFactory.decodeFile(photoFile.absolutePath))
        }
        photo.layoutParams=android.widget.LinearLayout.LayoutParams(-1,280)
        box.addView(photo)

        val name=android.widget.EditText(this@MainActivity)
        name.hint="Student name (optional)"
        name.setText(p.optString("name"))
        box.addView(name)

        val id=android.widget.EditText(this@MainActivity)
        id.hint="Student ID (optional)"
        id.setText(p.optString("studentId"))
        box.addView(id)

        val notes=android.widget.EditText(this@MainActivity)
        notes.hint="Caregiver / SLP notes"
        notes.setText(p.optString("notes"))
        notes.minLines=4
        box.addView(notes)

        val take=android.widget.Button(this@MainActivity)
        take.text="Choose Student Photo"
        take.setOnClickListener {
            val intent=Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.type="image/*"
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            startActivityForResult(intent, 2201)
        }
        box.addView(take)

        android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Student Profile")
            .setView(box)
            .setNegativeButton("Cancel",null)
            .setPositiveButton("Save") { _,_ ->
                saveStudentProfile(name.text.toString(),id.text.toString(),notes.text.toString())
            }.create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
    }

    override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?) {
        super.onActivityResult(requestCode,resultCode,data)
        if (requestCode==2201 && resultCode==RESULT_OK) {
            val uri=data?.data ?: return
            try {
                contentResolver.openInputStream(uri)?.use { input ->
                    File(studentDir(),"student_photo.jpg").outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                android.widget.Toast.makeText(this@MainActivity,"Student photo saved.",android.widget.Toast.LENGTH_SHORT).show()
            } catch (_:Exception) {
                android.widget.Toast.makeText(this@MainActivity,"Could not save photo.",android.widget.Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun buildStudentReportPdf() {
        val p=loadStudentProfile()
        val name=p.optString("name").ifBlank { "Student" }
        val id=p.optString("studentId")
        val notes=p.optString("notes")
        val history=File(filesDir,"dialogue_history")
        val sessions=if(history.exists()) history.listFiles()?.filter{it.isDirectory}?:emptyList() else emptyList()

        val wordCounts=mutableMapOf<String,Int>()
        val soundCounts=mutableMapOf<String,Int>()
        sessions.forEach { s ->
            val f=File(s,"analysis.json")
            if(!f.exists()) return@forEach
            val json=f.readText()
            val rx=Regex("""\{\s*"word"\s*:\s*"([^"]+)".*?"missingInitial"\s*:\s*"([^"]*)".*?"possibleInitialOmission"\s*:\s*(true|false).*?\}""",setOf(RegexOption.DOT_MATCHES_ALL))
            rx.findAll(json).forEach { m ->
                if(m.groupValues[3].equals("true",true)) {
                    val w=m.groupValues[1]
                    val sound=m.groupValues[2]
                    wordCounts[w]=(wordCounts[w]?:0)+1
                    if(sound.isNotBlank()) soundCounts[sound]=(soundCounts[sound]?:0)+1
                }
            }
        }

        val doc=PdfDocument()
        val page=doc.startPage(PdfDocument.PageInfo.Builder(612,792,1).create())
        val c=page.canvas
        val paint=android.graphics.Paint()
        paint.textSize=22f
        c.drawText("First Sound Helper — Student Report",32f,48f,paint)
        paint.textSize=16f
        c.drawText("Student: $name",32f,82f,paint)
        if(id.isNotBlank()) c.drawText("Student ID: $id",32f,106f,paint)
        c.drawText("Recordings analyzed: ${sessions.size}",32f,130f,paint)

        paint.textSize=18f
        c.drawText("Most frequent possible missing initial sounds",32f,170f,paint)
        paint.textSize=15f
        var y=198f
        soundCounts.entries.sortedByDescending{it.value}.take(10).forEach {
            c.drawText("${it.key} — ${it.value} possible omission(s)",48f,y,paint); y+=22f
        }

        paint.textSize=18f
        c.drawText("Words with repeated possible omissions",32f,y+18f,paint)
        paint.textSize=15f
        y+=48f
        wordCounts.entries.sortedByDescending{it.value}.take(10).forEach {
            c.drawText("${it.key} — ${it.value} time(s)",48f,y,paint); y+=22f
        }

        if(notes.isNotBlank()) {
            paint.textSize=18f
            c.drawText("Caregiver / SLP notes",32f,700f,paint)
            paint.textSize=13f
            val noteLine=notes.replace("\n"," ").take(90)
            c.drawText(noteLine,32f,724f,paint)
        }
        paint.textSize=11f
        c.drawText("This report summarizes app-generated observations and is not a clinical diagnosis.",32f,770f,paint)
        doc.finishPage(page)

        val reports=File(filesDir,"reports")
        if(!reports.exists()) reports.mkdirs()
        val stamp=java.text.SimpleDateFormat("yyyyMMdd_HHmmss",java.util.Locale.US).format(java.util.Date())
        val file=File(reports,"${name.replace(Regex("[^A-Za-z0-9_-]"),"_")}_$stamp.pdf")
        FileOutputStream(file).use { doc.writeTo(it) }
        doc.close()

        android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Report created")
            .setMessage("Saved to the app's private report storage:\n${file.name}")
            .setPositiveButton("OK",null)
            .create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
    }

    private fun showStudentTools() {
        android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Student & Reports")
            .setItems(arrayOf("Student Profile / Photo","Create Printable Report")) { _,which ->
                if(which==0) showStudentProfile() else buildStudentReportPdf()
            }.create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
    }

    // ---------------- Live Speech ----------------
    private var liveSpeechRecognizer: SpeechRecognizer? = null
    private var liveListening = false
    private var pendingAnalyzeContext: String = ""
    private val liveIndicatorHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private var liveIndicatorBright = true
    private val liveIndicatorFlash = object : Runnable {
        override fun run() {
            val indicator = findViewById<android.widget.TextView?>(R.id.liveStatusIndicator)
            if (liveListening && indicator != null) {
                liveIndicatorBright = !liveIndicatorBright
                indicator.alpha = if (liveIndicatorBright) 1.0f else 0.28f
                liveIndicatorHandler.postDelayed(this, 500)
            }
        }
    }

    private fun setLiveIndicator(active: Boolean, voiceDetected: Boolean = false) {
        val indicator = findViewById<android.widget.TextView?>(R.id.liveStatusIndicator) ?: return
        liveIndicatorHandler.removeCallbacks(liveIndicatorFlash)
        if (active) {
            indicator.visibility = android.view.View.VISIBLE
            indicator.alpha = 1.0f
            indicator.text = if (voiceDetected) "● LIVE — Voice detected" else "● LIVE — Listening"
            liveIndicatorBright = true
            liveIndicatorHandler.postDelayed(liveIndicatorFlash, 500)
        } else {
            indicator.alpha = 1.0f
            indicator.visibility = android.view.View.GONE
        }
    }

    private val liveMissingSoundCounts = java.util.LinkedHashMap<String, Int>()
    private val liveCandidateWordCounts = java.util.LinkedHashMap<String, Int>()
    private var liveSessionStartMs = 0L
    private var liveObservationCount = 0
    private var liveLastHeard = ""
    private var liveAudioRecord: AudioRecord? = null
    private var liveAudioThread: Thread? = null
    private var liveBuffer = java.io.ByteArrayOutputStream()
    private var liveChunkStartMs = 0L
    private val liveHandler = Handler(Looper.getMainLooper())
    private val liveExecutor = Executors.newSingleThreadExecutor()
    private val liveChunkMs = 2000L

    private fun startLiveSpeechMode() {
        if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(android.Manifest.permission.RECORD_AUDIO), 4101)
            return
        }

        liveListening = true
        setLiveIndicator(active = true)
        liveSessionStartMs = System.currentTimeMillis()
        liveMissingSoundCounts.clear()
        liveCandidateWordCounts.clear()
        liveObservationCount = 0
        liveLastHeard = ""
        liveChunkStartMs = System.currentTimeMillis()
        liveBuffer.reset()

        val dialog = android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Live Speech")
            .setMessage("Listening…\n\nHeard: —\n\nPossible missing first sound: —\n\nLive audio is analyzed in short chunks. Audio is not saved unless you choose Save Session.")
            .setNegativeButton("Stop") { _, _ -> stopLiveSpeechMode(showSummary = true) }
            .setOnDismissListener { if (liveListening) stopLiveSpeechMode() }
            .create()
        dialog.setCanceledOnTouchOutside(false)
        dialog.create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
        styleUnifiedDialog(dialog)

        val messageView = dialog.findViewById<android.widget.TextView>(android.R.id.message)
        val recognizer = if (SpeechRecognizer.isRecognitionAvailable(this)) SpeechRecognizer.createSpeechRecognizer(this) else null
        liveSpeechRecognizer = recognizer

        if (recognizer == null) {
            liveListening = false
            setLiveIndicator(active = false)
            dialog.setMessage("Live speech recognition is not available on this device.")
            return
        }

        recognizer.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: android.os.Bundle?) {
                if (liveListening) dialog.setMessage("Listening…\n\nHeard: —\n\nPossible missing first sound: —\n\nSpeak naturally.")
            }
            override fun onBeginningOfSpeech() {
                if (liveListening) setLiveIndicator(active = true, voiceDetected = true)
            }
            override fun onRmsChanged(rmsdB: Float) {
                if (liveListening) {
                    setLiveIndicator(active = true, voiceDetected = rmsdB > 3.5f)
                }
            }
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {
                if (liveListening) {
                    setLiveIndicator(active = true, voiceDetected = false)
                    restartLiveRecognizer()
                }
            }
            override fun onError(error: Int) {
                if (liveListening) {
                    // Avoid tight retry loops for permanent/request errors.
                    if (error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS ||
                        error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY) {
                        stopLiveSpeechMode()
                    } else {
                        restartLiveRecognizer()
                    }
                }
            }
            override fun onResults(results: android.os.Bundle?) {
                val heard = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()
                if (!heard.isNullOrBlank()) {
                    liveLastHeard = heard
                    dialog.setMessage("Listening…\n\nHeard: $heard\n\nPossible missing first sound: analyzing…")
                    analyzeLiveTextContext(heard, dialog)
                }
                if (liveListening) restartLiveRecognizer()
            }
            override fun onPartialResults(partialResults: android.os.Bundle?) {
                val heard = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()
                if (!heard.isNullOrBlank() && liveListening) {
                    liveLastHeard = heard
                    dialog.setMessage("Listening…\n\nHeard: $heard\n\nPossible missing first sound: analyzing…")
                }
            }
            override fun onEvent(eventType: Int, params: android.os.Bundle?) {}
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.US)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
        }
        recognizer.startListening(intent)

        startLiveAudioCapture(dialog)
    }

    private fun restartLiveRecognizer() {
        if (!liveListening) return
        liveHandler.postDelayed({
            if (!liveListening) return@postDelayed
            try {
                val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.US)
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                }
                liveSpeechRecognizer?.startListening(intent)
            } catch (_: Exception) {
                // A later cycle will retry while live mode remains active.
            }
        }, 250L)
    }

    private fun startLiveAudioCapture(dialog: android.app.AlertDialog) {
        liveAudioThread = Thread {
            val sampleRate = 16000
            val minBuf = AudioRecord.getMinBufferSize(
                sampleRate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )
            val bufferSize = maxOf(minBuf, sampleRate / 2)
            val record = try {
                AudioRecord(
                    MediaRecorder.AudioSource.VOICE_RECOGNITION,
                    sampleRate,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                    bufferSize
                )
            } catch (_: Exception) {
                null
            }
            if (record == null || record.state != AudioRecord.STATE_INITIALIZED) {
                liveHandler.post {
                    if (liveListening) dialog.setMessage("Listening…\n\nLive audio capture could not start on this device.\n\nSpeech recognition may still work.")
                }
                return@Thread
            }
            liveAudioRecord = record
            try {
                record.startRecording()
                val pcm = ByteArray(bufferSize)
                while (liveListening) {
                    val n = record.read(pcm, 0, pcm.size)
                    if (n > 0) {
                        synchronized(liveBuffer) {
                            liveBuffer.write(pcm, 0, n)
                        }
                        if (System.currentTimeMillis() - liveChunkStartMs >= liveChunkMs) {
                            val chunk = synchronized(liveBuffer) {
                                val b = liveBuffer.toByteArray()
                                liveBuffer.reset()
                                b
                            }
                            liveChunkStartMs = System.currentTimeMillis()
                            if (chunk.size >= sampleRate * 2 / 2) {
                                submitLiveAudioChunk(chunk, dialog)
                            }
                        }
                    }
                }
            } finally {
                try { record.stop() } catch (_: Exception) {}
                record.release()
                liveAudioRecord = null
            }
        }.apply { start() }
    }

    private fun submitLiveAudioChunk(pcm: ByteArray, dialog: android.app.AlertDialog) {
        // Convert PCM16 mono 16 kHz to WAV and send it to the configured Parent PC.
        val base = parentPcApiBase()
        if (base.isBlank()) {
            liveHandler.post {
                if (liveListening) dialog.setMessage("Parent PC is not configured.\n\nOpen Parent PC Connection on the main screen and save the local PC address.")
            }
            return
        }
        liveExecutor.execute {
            try {
                val wav = pcmToWavBytes(pcm, 16000, 1, 16)
                val liveRecordingId = UUID.randomUUID().toString()
                val client = OkHttpClient.Builder()
                    .connectTimeout(7, TimeUnit.SECONDS)
                    .readTimeout(12, TimeUnit.SECONDS)
                    .build()
                val body = MultipartBody.Builder().setType(MultipartBody.FORM)
                    .addFormDataPart("context", liveLastHeard)
                    .addFormDataPart("session_id", currentSessionId)
                    .addFormDataPart("recording_id", liveRecordingId)
                    .addFormDataPart("speaker_id", speakerId())
                    .addFormDataPart("audio", "live.wav", wav.toRequestBody("audio/wav".toMediaType()))
                    .build()
                val req = Request.Builder().url("$base/v1/analyze-audio").post(body).build()
                client.newCall(req).execute().use { response ->
                    val responseBody = response.body?.string().orEmpty()
                    if (!response.isSuccessful) return@use
                    val obj = org.json.JSONObject(responseBody)
                    val candidates = obj.optJSONArray("candidates")
                    val best = if (candidates != null && candidates.length() > 0) candidates.getJSONObject(0) else null
                    val missing = best?.optString("missingInitial", "") ?: ""
                    val word = best?.optString("word", "") ?: ""
                    if (missing.isNotBlank() && word.isNotBlank()) {
                        synchronized(this@MainActivity) {
                            liveMissingSoundCounts[missing] = (liveMissingSoundCounts[missing] ?: 0) + 1
                            liveCandidateWordCounts[word.lowercase(java.util.Locale.US)] =
                                (liveCandidateWordCounts[word.lowercase(java.util.Locale.US)] ?: 0) + 1
                            liveObservationCount += 1
                        }
                        liveHandler.post {
                            if (liveListening) {
                                val current = dialog.findViewById<android.widget.TextView>(android.R.id.message)?.text?.toString() ?: "Listening…"
                                val heardLine = current.substringAfter("Heard:", "—").substringBefore("\n").trim()
                                dialog.setMessage("Listening…\n\nHeard: $heardLine\n\nPossible missing first sound: $missing\nPossible word: $word\n\nThis is a probabilistic suggestion, not a diagnosis.")
                            }
                        }
                    }
                }
            } catch (_: Exception) {
                // Live mode is best-effort. Keep listening and allow the next chunk to retry.
            }
        }
    }

    private fun analyzeLiveTextContext(heard: String, dialog: android.app.AlertDialog) {
        // Phrase/word suggestions remain driven by the same saved/local features.
        // The phoneme endpoint is responsible for audio evidence; this hook avoids treating
        // partial speech-recognition text as proof of an omitted consonant.
    }
    private fun stopLiveSpeechMode(showSummary: Boolean = false) {
        liveListening = false
        setLiveIndicator(active = false)
        try { liveSpeechRecognizer?.stopListening() } catch (_: Exception) {}
        try { liveSpeechRecognizer?.destroy() } catch (_: Exception) {}
        liveSpeechRecognizer = null
        try { liveAudioRecord?.stop() } catch (_: Exception) {}
        liveAudioRecord = null
        liveHandler.removeCallbacksAndMessages(null)
        synchronized(liveBuffer) { liveBuffer.reset() }

        if (showSummary) {
            showLiveSessionSummary()
        }
    }

    private fun showLiveSessionSummary() {
        val durationSec = ((System.currentTimeMillis() - liveSessionStartMs) / 1000L).coerceAtLeast(0L)
        val sounds = synchronized(this) { liveMissingSoundCounts.toList().sortedByDescending { it.second } }
        val words = synchronized(this) { liveCandidateWordCounts.toList().sortedByDescending { it.second } }

        val message = StringBuilder()
            .append("Session length: ").append(formatLiveDuration(durationSec))
            .append("\nObservations: ").append(liveObservationCount).append("\n\n")
            .append("Possible missing initial sounds\n")

        if (sounds.isEmpty()) {
            message.append("No phoneme observations were returned.\n")
        } else {
            sounds.take(8).forEach { (sound, count) ->
                message.append("• ").append(sound).append(" — ").append(count).append("\n")
            }
        }

        message.append("\nRepeated candidate words\n")
        if (words.isEmpty()) {
            message.append("No candidate words were returned.\n")
        } else {
            words.take(10).forEach { (word, count) ->
                message.append("• ").append(word).append(" — ").append(count).append("\n")
            }
        }

        message.append("\nHeard most recently: ")
            .append(if (liveLastHeard.isBlank()) "—" else liveLastHeard)
            .append("\n\nThe playback uses the live candidate word to create a possible corrected sentence. It is only a suggestion.\n\nThis is a descriptive, probabilistic summary, not a diagnosis or clinical assessment.")

        val correctedSentence = buildCorrectedSentence(liveLastHeard, sounds, words)

        val dialog = android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Live Session Summary")
            .setMessage(message.toString())
            .setPositiveButton("Done", null)
            .setNeutralButton("Save Session Summary", null)
            .setNegativeButton("Play Suggested Sentence", null)
            .create()

        dialog.setOnShowListener {
            dialog.getButton(android.app.AlertDialog.BUTTON_NEUTRAL).setOnClickListener {
                val ok = saveLiveSessionSummary(durationSec, sounds, words, liveLastHeard)
                android.widget.Toast.makeText(
                    this,
                    if (ok) "Session summary saved." else "Could not save session summary.",
                    android.widget.Toast.LENGTH_SHORT
                ).create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
                dialog.dismiss()
            }

            dialog.getButton(android.app.AlertDialog.BUTTON_NEGATIVE).setOnClickListener {
                if (correctedSentence.isBlank()) {
                    android.widget.Toast.makeText(
                        this,
                        "No corrected sentence is available yet.",
                        android.widget.Toast.LENGTH_SHORT
                    ).create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
                } else {
                    val correctedWords = buildCorrectedSentenceWords(liveLastHeard, sounds, words)
                    val spliced = playSplicedSentence(correctedWords)
                    if (!spliced) {
                        speakCorrectedSentence(correctedSentence)
                        android.widget.Toast.makeText(
                            this,
                            "Student word recordings were incomplete, so the app used TTS.",
                            android.widget.Toast.LENGTH_SHORT
                        ).create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
                    }
                }
            }
        }
        dialog.create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
        styleUnifiedDialog(dialog)
    }



    private fun showPersonalWordBank() {
        if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(android.Manifest.permission.RECORD_AUDIO), 4201)
            return
        }

        loadStudentWordBank()

        val layout = android.widget.LinearLayout(this@MainActivity).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(40, 24, 40, 16)
        }

        val wordInput = android.widget.EditText(this@MainActivity).apply {
            hint = "Word (example: cat)"
            isSingleLine = true
        }
        layout.addView(wordInput)

        val recordButton = android.widget.Button(this@MainActivity).apply {
            text = "Record Student Word"
        }
        layout.addView(recordButton)

        val list = android.widget.LinearLayout(this@MainActivity).apply {
            orientation = android.widget.LinearLayout.VERTICAL
        }
        layout.addView(list)

        val scroll = android.widget.ScrollView(this@MainActivity).apply {
            addView(list)
        }
        layout.removeView(list)
        layout.addView(scroll, android.widget.LinearLayout.LayoutParams(
            android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
            0, 1f
        ))

        val dialog = android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Personal Word Bank")
            .setView(layout)
            .setPositiveButton("Done", null)
            .create()
        wordBankDialog = dialog

        fun refreshList() {
            loadStudentWordBank()
            list.removeAllViews()
            if (studentWordBank.isEmpty()) {
                list.addView(android.widget.TextView(this@MainActivity).apply {
                    text = "No student word recordings yet.\n\nRecord words that can be reused when the app builds suggested sentences."
                    setPadding(0, 24, 0, 24)
                })
                return
            }

            studentWordBank.toSortedMap().forEach { (word, file) ->
                val row = android.widget.LinearLayout(this@MainActivity).apply {
                    orientation = android.widget.LinearLayout.HORIZONTAL
                    setPadding(0, 8, 0, 8)
                }
                val label = android.widget.TextView(this@MainActivity).apply {
                    text = word
                    textSize = 18f
                    layoutParams = android.widget.LinearLayout.LayoutParams(0, -2, 1f)
                }
                val play = android.widget.Button(this@MainActivity).apply {
                    text = "Play"
                    setOnClickListener {
                        if (!playStudentWord(word)) {
                            android.widget.Toast.makeText(this@MainActivity, "Could not play recording.", android.widget.Toast.LENGTH_SHORT).show()
                        }
                    }
                }
                val delete = android.widget.Button(this@MainActivity).apply {
                    text = "Delete"
                    setOnClickListener {
                        file.delete()
                        refreshList()
                    }
                }
                row.addView(label)
                row.addView(play)
                row.addView(delete)
                list.addView(row)
            }
        }

        recordButton.setOnClickListener {
            val word = wordInput.text.toString().trim().lowercase(java.util.Locale.US)
            if (word.isBlank() || !word.matches(Regex("[a-z][a-z'-]*"))) {
                wordInput.error = "Enter one English word"
                return@setOnClickListener
            }
            if (wordBankRecorder != null) return@setOnClickListener

            val dir = java.io.File(filesDir, "student_word_bank")
            if (!dir.exists()) dir.mkdirs()
            val safe = word.replace(Regex("[^a-z0-9_-]"), "_")
            val file = java.io.File(dir, "${safe}_${System.currentTimeMillis()}.wav")
            wordBankRecordingFile = file

            try {
                val recorder = MediaRecorder(this@MainActivity).apply {
                    setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION)
                    setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                    setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                    setOutputFile(file.absolutePath)
                    prepare()
                    start()
                }
                wordBankRecorder = recorder
                recordButton.text = "Stop Recording"
                wordInput.isEnabled = false
                android.widget.Toast.makeText(this@MainActivity, "Say “$word” once.", android.widget.Toast.LENGTH_SHORT).show()

                recordButton.setOnClickListener {
                    try { wordBankRecorder?.stop() } catch (_: Exception) {}
                    try { wordBankRecorder?.release() } catch (_: Exception) {}
                    wordBankRecorder = null

                    // The recording was encoded as MPEG-4/AAC; move it to a WAV-like
                    // word-bank filename only if it remains playable by MediaPlayer.
                    // Keep the actual extension accurate.
                    val finalFile = file
                    if (finalFile.exists() && finalFile.length() > 0) {
                        studentWordBank[word] = finalFile
                    } else {
                        finalFile.delete()
                    }

                    recordButton.text = "Record Student Word"
                    wordInput.isEnabled = true
                    wordInput.text.clear()
                    refreshList()
                    recordButton.setOnClickListener {
                        val w = wordInput.text.toString().trim().lowercase(java.util.Locale.US)
                        if (w.isBlank() || !w.matches(Regex("[a-z][a-z'-]*"))) {
                            wordInput.error = "Enter one English word"
                        } else {
                            startWordBankRecording(w, recordButton, wordInput, list)
                        }
                    }
                }
            } catch (_: Exception) {
                wordBankRecorder = null
                file.delete()
                android.widget.Toast.makeText(this@MainActivity, "Could not start recording.", android.widget.Toast.LENGTH_SHORT).show()
            }
        }

        refreshList()
        dialog.setOnDismissListener {
            try { wordBankRecorder?.stop() } catch (_: Exception) {}
            try { wordBankRecorder?.release() } catch (_: Exception) {}
            wordBankRecorder = null
            wordBankDialog = null
        }
        dialog.create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
        styleUnifiedDialog(dialog)
    }

    private fun startWordBankRecording(
        word: String,
        button: android.widget.Button,
        input: android.widget.EditText,
        list: android.widget.LinearLayout
    ) {
        val dir = java.io.File(filesDir, "student_word_bank")
        if (!dir.exists()) dir.mkdirs()
        val file = java.io.File(dir, "${word.replace(Regex("[^a-z0-9_-]"), "_")}_${System.currentTimeMillis()}.m4a")
        wordBankRecordingFile = file

        try {
            val recorder = MediaRecorder(this@MainActivity).apply {
                setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(file.absolutePath)
                prepare()
                start()
            }
            wordBankRecorder = recorder
            button.text = "Stop Recording"
            input.isEnabled = false
            android.widget.Toast.makeText(this@MainActivity, "Say “$word” once.", android.widget.Toast.LENGTH_SHORT).show()

            button.setOnClickListener {
                try { wordBankRecorder?.stop() } catch (_: Exception) {}
                try { wordBankRecorder?.release() } catch (_: Exception) {}
                wordBankRecorder = null
                if (file.exists() && file.length() > 0) {
                    studentWordBank[word] = file
                } else {
                    file.delete()
                }
                button.text = "Record Student Word"
                input.isEnabled = true
                input.text.clear()
                list.removeAllViews()
                loadStudentWordBank()
                if (studentWordBank.isEmpty()) {
                    list.addView(android.widget.TextView(this@MainActivity).apply {
                        text = "No student word recordings yet."
                    })
                } else {
                    studentWordBank.toSortedMap().forEach { (w, f) ->
                        val row = android.widget.LinearLayout(this@MainActivity).apply {
                            orientation = android.widget.LinearLayout.HORIZONTAL
                        }
                        row.addView(android.widget.TextView(this@MainActivity).apply {
                            text = w
                            textSize = 18f
                            layoutParams = android.widget.LinearLayout.LayoutParams(0, -2, 1f)
                        })
                        row.addView(android.widget.Button(this@MainActivity).apply {
                            text = "Play"
                            setOnClickListener { playStudentWord(w) }
                        })
                        row.addView(android.widget.Button(this@MainActivity).apply {
                            text = "Delete"
                            setOnClickListener {
                                f.delete()
                                loadStudentWordBank()
                                button.performClick()
                            }
                        })
                        list.addView(row)
                    }
                }
                button.setOnClickListener {
                    val w = input.text.toString().trim().lowercase(java.util.Locale.US)
                    if (w.isBlank() || !w.matches(Regex("[a-z][a-z'-]*"))) input.error = "Enter one English word"
                    else startWordBankRecording(w, button, input, list)
                }
            }
        } catch (_: Exception) {
            file.delete()
            android.widget.Toast.makeText(this@MainActivity, "Could not start recording.", android.widget.Toast.LENGTH_SHORT).show()
        }
    }

    private fun loadStudentWordBank() {
        studentWordBank.clear()
        val dir = java.io.File(filesDir, "student_word_bank")
        if (!dir.exists()) return
        dir.listFiles()?.filter { it.isFile && (it.extension.equals("wav", ignoreCase = true) || it.extension.equals("m4a", ignoreCase = true)) }?.forEach { file ->
            val word = file.nameWithoutExtension.substringBeforeLast("_").trim().lowercase(java.util.Locale.US)
            if (word.isNotBlank()) studentWordBank[word] = file
        }
    }

    private fun findStudentWordRecording(word: String): java.io.File? {
        loadStudentWordBank()
        val normalized = word.lowercase(java.util.Locale.US)
            .trim(' ', '.', ',', '!', '?', ';', ':', '"', '\'')
        return studentWordBank[normalized]
    }

    private fun saveStudentWordRecording(word: String, wavFile: java.io.File): java.io.File? {
        return try {
            val dir = java.io.File(filesDir, "student_word_bank")
            if (!dir.exists()) dir.mkdirs()
            val safeWord = word.lowercase(java.util.Locale.US)
                .replace(Regex("[^a-z0-9_-]"), "_")
            if (safeWord.isBlank()) return null
            val destination = java.io.File(
                dir,
                "${safeWord}_${System.currentTimeMillis()}.wav"
            )
            wavFile.copyTo(destination, overwrite = true)
            studentWordBank[safeWord] = destination
            destination
        } catch (_: Exception) {
            null
        }
    }

    private fun playStudentWord(word: String): Boolean {
        val file = findStudentWordRecording(word) ?: return false
        return try {
            val player = android.media.MediaPlayer().apply {
                setDataSource(file.absolutePath)
                setOnCompletionListener { it.release() }
                setOnErrorListener { mp, _, _ -> mp.release(); true }
                prepare()
                start()
            }
            true
        } catch (_: Exception) {
            false
        }
    }

    private fun playSplicedSentence(words: List<String>): Boolean {
        val recordings = words.map { it to findStudentWordRecording(it) }
        if (recordings.any { it.second == null }) return false

        // Play each student-recorded word sequentially with a short natural pause.
        val handler = android.os.Handler(android.os.Looper.getMainLooper())
        var index = 0

        fun playNext() {
            if (index >= recordings.size) return
            val file = recordings[index].second ?: return
            try {
                val player = android.media.MediaPlayer().apply {
                    setDataSource(file.absolutePath)
                    setOnCompletionListener {
                        it.release()
                        index += 1
                        handler.postDelayed({ playNext() }, 180L)
                    }
                    setOnErrorListener { mp, _, _ ->
                        mp.release()
                        true
                    }
                    prepare()
                    start()
                }
            } catch (_: Exception) {
                // Fall back to normal TTS if a clip cannot be played.
            }
        }

        playNext()
        return true
    }

    private fun buildCorrectedSentenceWords(
        latestHeard: String,
        sounds: List<Pair<String, Int>>,
        words: List<Pair<String, Int>>
    ): List<String> {
        val sentence = latestHeard.trim()
        if (sentence.isBlank()) {
            return if (words.isNotEmpty()) listOf(words.first().first) else emptyList()
        }
        if (words.isEmpty()) return sentence.split(Regex("\\s+"))

        val candidate = words.first().first.trim()
        if (candidate.isBlank()) return sentence.split(Regex("\\s+"))

        val candidateLower = candidate.lowercase(java.util.Locale.US)
        val withoutInitial = candidateLower.dropInitialConsonantForPlayback()
        val tokens = sentence.split(Regex("\\s+")).toMutableList()

        for (i in tokens.indices) {
            val raw = tokens[i]
            val leading = raw.takeWhile { !it.isLetterOrDigit() }
            val trailing = raw.takeLastWhile { !it.isLetterOrDigit() }
            val core = raw.removePrefix(leading).removeSuffix(trailing)
            val normalized = core.lowercase(java.util.Locale.US)
            if (normalized == candidateLower ||
                (withoutInitial.isNotBlank() && normalized == withoutInitial)
            ) {
                tokens[i] = leading + candidate + trailing
                break
            }
        }
        return tokens
    }

    private fun addSavedRecordingToWordBank(word: String, recordingFile: java.io.File): Boolean {
        return saveStudentWordRecording(word, recordingFile) != null
    }

    private fun speakCorrectedSentence(sentence: String) {
        if (sentence.isBlank()) return
        if (correctedSentenceTts == null) {
            correctedSentenceTts = TextToSpeech(this@MainActivity) { status ->
                correctedSentenceReady = status == TextToSpeech.SUCCESS
                if (correctedSentenceReady) {
                    correctedSentenceTts?.language = Locale.US
                    correctedSentenceTts?.speak(
                        sentence,
                        TextToSpeech.QUEUE_FLUSH,
                        null,
                        "corrected_sentence"
                    )
                }
            }
        } else {
            correctedSentenceTts?.language = Locale.US
            correctedSentenceTts?.speak(
                sentence,
                TextToSpeech.QUEUE_FLUSH,
                null,
                "corrected_sentence"
            )
        }
    }
    private fun buildCorrectedSentence(
        latestHeard: String,
        sounds: List<Pair<String, Int>>,
        words: List<Pair<String, Int>>
    ): String {
        val sentence = latestHeard.trim()
        if (sentence.isBlank()) {
            return if (words.isNotEmpty()) words.first().first else ""
        }
        if (words.isEmpty()) return sentence

        val candidate = words.first().first.trim()
        if (candidate.isBlank()) return sentence

        // Reconstruct a possible corrected sentence by replacing the first
        // recognized token that matches the candidate after its initial
        // consonant has been omitted.
        val tokens = sentence.split(Regex("\\s+")).toMutableList()
        val candidateLower = candidate.lowercase(java.util.Locale.US)
        val candidateWithoutInitial = candidateLower.dropInitialConsonantForPlayback()

        var replaced = false
        for (i in tokens.indices) {
            val raw = tokens[i]
            val leading = raw.takeWhile { !it.isLetterOrDigit() }
            val trailing = raw.takeLastWhile { !it.isLetterOrDigit() }
            val core = raw.removePrefix(leading).removeSuffix(trailing)
            val normalized = core.lowercase(java.util.Locale.US)

            if (normalized == candidateLower ||
                (candidateWithoutInitial.isNotBlank() && normalized == candidateWithoutInitial)
            ) {
                tokens[i] = leading + candidate + trailing
                replaced = true
                break
            }
        }

        if (replaced) return tokens.joinToString(" ")

        // If speech recognition produced a shortened token that differs
        // slightly, append the candidate only when the sentence does not
        // already contain it. This avoids silently inventing extra words.
        if (!tokens.any { it.trim(' ', '.', ',', '!', '?').equals(candidate, ignoreCase = true) }) {
            return sentence
        }
        return sentence
    }

    private fun String.dropInitialConsonantForPlayback(): String {
        val s = this.lowercase(java.util.Locale.US)
        if (s.length <= 1) return ""
        val two = s.take(2)
        return if (two == "ch" || two == "sh" || two == "th" || two == "wh" || two == "ph" ||
            two == "br" || two == "cr" || two == "dr" || two == "fr" || two == "gr" ||
            two == "pr" || two == "tr" || two == "bl" || two == "cl" || two == "fl" ||
            two == "gl" || two == "pl" || two == "sl" || two == "sm" || two == "sn" ||
            two == "sp" || two == "st" || two == "sk"
        ) {
            s.drop(2)
        } else {
            s.drop(1)
        }
    }



    private fun saveLiveSessionSummary(
        durationSec: Long,
        sounds: List<Pair<String, Int>>,
        words: List<Pair<String, Int>>,
        latestHeard: String
    ): Boolean {
        return try {
            val dir = java.io.File(filesDir, "live_session_summaries")
            if (!dir.exists()) dir.mkdirs()

            val stamp = java.text.SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", java.util.Locale.US)
                .format(java.util.Date())
            val file = java.io.File(dir, "live_session_$stamp.json")

            val json = org.json.JSONObject()
                .put("savedAt", System.currentTimeMillis())
                .put("sessionDurationSeconds", durationSec)
                .put("observationCount", liveObservationCount)
                .put("latestHeard", latestHeard)
                .put("note", "Descriptive probabilistic session summary; not a diagnosis or clinical assessment.")

            val soundArray = org.json.JSONArray()
            sounds.forEach { (sound, count) ->
                soundArray.put(org.json.JSONObject().put("sound", sound).put("count", count))
            }
            json.put("possibleMissingInitialSounds", soundArray)

            val wordArray = org.json.JSONArray()
            words.forEach { (word, count) ->
                wordArray.put(org.json.JSONObject().put("word", word).put("count", count))
            }
            json.put("candidateWords", wordArray)

            file.writeText(json.toString(2))
            true
        } catch (_: Exception) {
            false
        }
    }

    private fun formatLiveDuration(seconds: Long): String {
        val minutes = seconds / 60
        val secs = seconds % 60
        return if (minutes > 0) "${minutes}m ${secs}s" else "${secs}s"
    }

    private fun pcmToWavBytes(pcm: ByteArray, sampleRate: Int, channels: Int, bitsPerSample: Int): ByteArray {
        val dataLen = pcm.size
        val byteRate = sampleRate * channels * bitsPerSample / 8
        val blockAlign = channels * bitsPerSample / 8
        val totalLen = 36 + dataLen
        val out = java.io.ByteArrayOutputStream(44 + dataLen)
        fun writeIntLE(v: Int) {
            out.write(byteArrayOf(
                (v and 0xff).toByte(),
                ((v shr 8) and 0xff).toByte(),
                ((v shr 16) and 0xff).toByte(),
                ((v shr 24) and 0xff).toByte()
            ))
        }
        fun writeShortLE(v: Int) {
            out.write(byteArrayOf((v and 0xff).toByte(), ((v shr 8) and 0xff).toByte()))
        }
        out.write("RIFF".toByteArray())
        writeIntLE(totalLen)
        out.write("WAVE".toByteArray())
        out.write("fmt ".toByteArray())
        writeIntLE(16)
        writeShortLE(1)
        writeShortLE(channels)
        writeIntLE(sampleRate)
        writeIntLE(byteRate)
        writeShortLE(blockAlign)
        writeShortLE(bitsPerSample)
        out.write("data".toByteArray())
        writeIntLE(dataLen)
        out.write(pcm)
        return out.toByteArray()
    }


    /**
     * Visual Sentence Builder
     *
     * Lets a student tap word tiles to build a sentence, remove tiles,
     * clear the sentence, and play the result. Student-recorded words from
     * the Personal Word Bank are used when available; otherwise Android TTS
     * provides a fallback.
     */
    private fun showVisualSentenceBuilder() {
        val dialog = android.app.Dialog(this@MainActivity)
        val root = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 20, 24, 20)
        }

        val title = TextView(this@MainActivity).apply {
            text = "Build a sentence"
            textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setPadding(0, 0, 0, 12)
        }
        root.addView(title)

        val help = TextView(this@MainActivity).apply {
            text = "Tap words below. Your sentence will appear at the top."
            textSize = 16f
            setPadding(0, 0, 0, 14)
        }
        root.addView(help)

        val sentenceScroll = HorizontalScrollView(this@MainActivity)
        val sentenceRow = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(4, 8, 4, 12)
        }
        sentenceScroll.addView(sentenceRow)
        root.addView(sentenceScroll, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ))

        val sentenceText = TextView(this@MainActivity).apply {
            text = "Tap a word to start."
            textSize = 21f
            setPadding(12, 12, 12, 12)
            setBackgroundColor(0xFFEFF4F8.toInt())
        }
        root.addView(sentenceText)

        val suggestionsLabel = TextView(this@MainActivity).apply {
            text = "Words"
            textSize = 18f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setPadding(0, 18, 0, 8)
        }
        root.addView(suggestionsLabel)

        val wordsScroll = ScrollView(this@MainActivity)
        val wordsGrid = android.widget.GridLayout(this@MainActivity).apply {
            columnCount = 3
            rowCount = android.widget.GridLayout.UNDEFINED
            useDefaultMargins = true
            setPadding(2, 2, 2, 2)
        }
        wordsScroll.addView(wordsGrid)
        root.addView(wordsScroll, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            0,
            1f
        ))

        val customWord = EditText(this@MainActivity).apply {
            hint = "Add a word"
            textSize = 17f
            isSingleLine = true
        }
        root.addView(customWord)

        val actionRow = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER
        }
        root.addView(actionRow)

        val speak = Button(this@MainActivity).apply { text = "▶ Play" }
        val backspace = Button(this@MainActivity).apply { text = "⌫ Remove" }
        val clear = Button(this@MainActivity).apply { text = "Clear" }
        val add = Button(this@MainActivity).apply { text = "Add" }
        actionRow.addView(speak)
        actionRow.addView(backspace)
        actionRow.addView(clear)
        actionRow.addView(add)

        // Child-friendly starter vocabulary. Keep this editable through the
        // student's own Personal Word Bank and custom-word field.
        val starterWords = linkedSetOf(
            "I", "want", "more", "help", "go", "stop", "play", "eat", "drink",
            "the", "a", "my", "mom", "dad", "teacher", "home", "school",
            "outside", "bathroom", "yes", "no", "please", "thank you",
            "cat", "dog", "ball", "car", "book"
        )
        starterWords.addAll(studentWordBank.keys)
        starterWords.addAll(loadCustomVocabulary())

        fun refreshSentence() {
            sentenceRow.removeAllViews()
            if (sentenceBuilderWords.isEmpty()) {
                sentenceText.text = "Tap a word to start."
            } else {
                sentenceText.text = sentenceBuilderWords.joinToString(" ")
                sentenceBuilderWords.forEachIndexed { index, word ->
                    val chip = Button(this@MainActivity).apply {
                        text = word
                        textSize = 16f
                        contentDescription = "Remove $word from sentence"
                        setOnClickListener {
                            sentenceBuilderWords.removeAt(index)
                            refreshSentence()
                        }
                    }
                    sentenceRow.addView(chip)
                }
            }
        }

        fun addWord(word: String) {
            val cleaned = word.trim()
            if (cleaned.isNotEmpty() && sentenceBuilderWords.size < 20) {
                sentenceBuilderWords.add(cleaned)
                customWord.text.clear()
                refreshSentence()
            }
        }

        fun addWordButton(word: String) {
            val b = Button(this@MainActivity).apply {
                text = word
                textSize = 17f
                minHeight = 52
                setOnClickListener { addWord(word) }
            }
            wordsGrid.addView(b)
        }

        starterWords.forEach { addWordButton(it) }

        add.setOnClickListener { addWord(customWord.text.toString()) }

        clear.setOnClickListener {
            sentenceBuilderWords.clear()
            refreshSentence()
        }

        backspace.setOnClickListener {
            if (sentenceBuilderWords.isNotEmpty()) {
                sentenceBuilderWords.removeAt(sentenceBuilderWords.lastIndex)
                refreshSentence()
            }
        }

        speak.setOnClickListener {
            val words = sentenceBuilderWords.toList()
            if (words.isEmpty()) return@setOnClickListener

            // Reuse the existing reconstructed sentence playback helper when
            // present, so Personal Word Bank recordings are preferred.
            val helper = this::class.java.declaredMethods.firstOrNull {
                it.name == "playReconstructedSentence" &&
                    it.parameterTypes.size == 1
            }
            if (helper != null) {
                try {
                    helper.isAccessible = true
                    helper.invoke(this, words.joinToString(" "))
                    return@setOnClickListener
                } catch (_: Throwable) {
                    // Fall through to local TTS.
                }
            }

            val ttsField = this::class.java.declaredFields.firstOrNull {
                it.name == "tts"
            }
            if (ttsField != null) {
                try {
                    ttsField.isAccessible = true
                    val engine = ttsField.get(this)
                    val speakMethod = engine?.javaClass?.methods?.firstOrNull {
                        it.name == "speak" && it.parameterTypes.size >= 2
                    }
                    if (speakMethod != null) {
                        speakMethod.invoke(
                            engine,
                            words.joinToString(" "),
                            android.speech.tts.TextToSpeech.QUEUE_FLUSH,
                            null,
                            "sentence_builder"
                        )
                        return@setOnClickListener
                    }
                } catch (_: Throwable) {
                    // Fall through to a new TTS instance.
                }
            }

            tts = android.speech.tts.TextToSpeech(this@MainActivity) { status ->
                if (status == android.speech.tts.TextToSpeech.SUCCESS) {
                    tts?.speak(
                        words.joinToString(" "),
                        android.speech.tts.TextToSpeech.QUEUE_FLUSH,
                        null,
                        "sentence_builder_fallback"
                    )
                }
            }
        }

        refreshSentence()
        dialog.setContentView(root)
        dialog.window?.setSoftInputMode(
            android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE
        )
        dialog.show()
        styleUnifiedDialog(dialog)
        dialog.window?.setLayout(
            (resources.displayMetrics.widthPixels * 0.94).toInt(),
            (resources.displayMetrics.heightPixels * 0.88).toInt()
        )
    }



    // ---------- Student support features ----------

    private fun supportPrefs() = getSharedPreferences("student_support", MODE_PRIVATE)

    private fun favoritePhrases(): MutableList<String> {
        val raw = supportPrefs().getString("favorite_phrases", "[]") ?: "[]"
        return try {
            val a = JSONArray(raw)
            MutableList(a.length()) { i -> a.getString(i) }
        } catch (_: Exception) { mutableListOf() }
    }

    private fun saveFavoritePhrases(items: List<String>) {
        val a = JSONArray()
        items.distinct().forEach { a.put(it) }
        supportPrefs().edit().putString("favorite_phrases", a.toString()).apply()
    }

    private fun customVocabularyFile(): File = File(filesDir, "custom_vocabulary.json")

    private fun loadCustomVocabulary(): MutableList<String> {
        val f = customVocabularyFile()
        if (!f.exists()) return mutableListOf()
        return try {
            val a = JSONArray(f.readText())
            MutableList(a.length()) { i -> a.getString(i) }
        } catch (_: Exception) { mutableListOf() }
    }

    private fun saveCustomVocabulary(items: List<String>) {
        val a = JSONArray()
        items.distinct().filter { it.isNotBlank() }.forEach { a.put(it.trim()) }
        customVocabularyFile().writeText(a.toString())
    }

    private fun showStudentCommunicationTools() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(popupDp(22), popupDp(18), popupDp(22), popupDp(22))
        }

        list.addView(popupHeader(
            "Student Communication Tools",
            "Choose the communication support that is easiest for the student right now.",
            "🧩"
        ))

        fun tool(icon: String, title: String, description: String, action: () -> Unit) {
            list.addView(popupActionButton(title, description, icon) {
                dialog.dismiss()
                action()
            })
        }

        tool("⭐", "Favorite Phrases", "Keep important phrases one tap away.") { showFavoritePhrases() }
        tool("🖼️", "Picture + Voice Choices", "Choose from visual options and hear the choice.") { showPictureVoiceChoices() }
        tool("🔁", "Try Again Practice", "Practice a word or phrase without pressure.") { showTryAgainPractice() }
        tool("☑️", "Choice Board", "Offer two to six simple choices.") { showChoiceBoard() }
        tool("💬", "Quick Communication Needs", "Fast access to help, break, yes, no, and more.") { showQuickCommunication() }
        tool("📈", "Visual Progress", "See saved practice and communication activity.") { showVisualProgress() }
        tool("📝", "Teacher / Caregiver Notes", "Keep local notes about helpful communication supports.") { showSupportNotes() }
        tool("📚", "Custom Vocabulary", "Add words that matter to this student.") { showCustomVocabulary() }
        tool("🔒", "Privacy & Offline", "Control analysis uploads and remove local student data.") { showPrivacyControls() }
        tool("🗣️", "Communication Modes", "Switch between speech, visual, text, and recorded voice.") { showCommunicationModes() }
        tool("🧩", "Visual Sentence Builder", "Build a sentence by tapping word tiles.") { showVisualSentenceBuilder() }

        list.addView(popupInfoCard(
            "Tip",
            "Customize these tools around the student's interests, routines, and communication goals.",
            "❤️"
        ))
        list.addView(popupActionButton("Close", null, "×") { dialog.dismiss() })

        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showFavoritePhrases() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(28, 20, 28, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Favorite Phrases"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        val favorites = favoritePhrases()

        fun render() {
            while (list.childCount > 1) list.removeViewAt(1)
            if (favorites.isEmpty()) {
                list.addView(TextView(this@MainActivity).apply {
                    text = "No favorites yet. Add important phrases below."
                    textSize = 17f; setPadding(0, 16, 0, 16)
                })
            } else {
                favorites.toList().forEach { phrase ->
                    val row = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.HORIZONTAL }
                    row.addView(TextView(this@MainActivity).apply {
                        text = phrase; textSize = 18f
                        layoutParams = LinearLayout.LayoutParams(0, -2, 1f)
                        setPadding(0, 10, 8, 10)
                    })
                    row.addView(Button(this@MainActivity).apply {
                        text = "▶"; setOnClickListener { speakCommunicationText(phrase) }
                    })
                    row.addView(Button(this@MainActivity).apply {
                        text = "Remove"
                        setOnClickListener {
                            favorites.remove(phrase); saveFavoritePhrases(favorites); render()
                        }
                    })
                    list.addView(row)
                }
            }
            list.addView(EditText(this@MainActivity).apply {
                hint = "Add favorite phrase"
                tag = "favorite_input"
            })
            list.addView(Button(this@MainActivity).apply {
                text = "Add Favorite"
                setOnClickListener {
                    val input = list.findViewWithTag<EditText>("favorite_input")
                    val p = input?.text?.toString()?.trim().orEmpty()
                    if (p.isNotBlank()) { favorites.add(p); saveFavoritePhrases(favorites); render() }
                }
            })
        }
        render()
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showPictureVoiceChoices() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Picture + Voice Choices"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "Visual symbols are optional supports. Tap a choice to hear it."
            textSize = 16f; setPadding(0, 8, 0, 16)
        })

        val choices = listOf(
            "🍎" to "eat", "🥤" to "drink", "🚽" to "bathroom", "🛝" to "outside",
            "🧸" to "play", "🛑" to "stop", "🙋" to "help", "💧" to "water",
            "😊" to "yes", "🙅" to "no", "🧑‍🏫" to "teacher", "🏠" to "home"
        )
        val grid = android.widget.GridLayout(this@MainActivity).apply { columnCount = 3; useDefaultMargins = true }
        choices.forEach { (emoji, word) ->
            grid.addView(Button(this@MainActivity).apply {
                text = "$emoji\n$word"; textSize = 18f; minHeight = 86
                setOnClickListener { speakCommunicationText(word) }
            })
        }
        list.addView(grid)
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showTryAgainPractice() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(28, 20, 28, 24)
        }
        val word = EditText(this@MainActivity).apply {
            hint = "Word or short phrase to practice"
            textSize = 18f
        }
        val prompt = TextView(this@MainActivity).apply {
            text = "Hear it, try it, and try again if you want. There is no pass/fail result."
            textSize = 17f; setPadding(0, 8, 0, 18)
        }
        val count = TextView(this@MainActivity).apply { textSize = 16f }
        var attempts = 0

        list.addView(TextView(this@MainActivity).apply { text = "Try Again Practice"; textSize = 24f; setTypeface(typeface, android.graphics.Typeface.BOLD) })
        list.addView(prompt); list.addView(word)
        list.addView(Button(this@MainActivity).apply {
            text = "🔊 Hear Example"
            setOnClickListener {
                val w = word.text.toString().trim()
                if (w.isNotBlank()) speakCommunicationText(w)
            }
        })
        list.addView(Button(this@MainActivity).apply {
            text = "🎙️ Try Again"
            setOnClickListener {
                attempts += 1
                count.text = "Practice attempts: $attempts"
                supportPrefs().edit().putInt("practice_attempts", supportPrefs().getInt("practice_attempts", 0) + 1).apply()
                Toast.makeText(this@MainActivity, "Nice try. You can try again or move on.", Toast.LENGTH_SHORT).show()
            }
        })
        list.addView(count)
        list.addView(Button(this@MainActivity).apply { text = "Done"; setOnClickListener { dialog.dismiss() } })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showChoiceBoard() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Choice Board"; textSize = 24f; setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "Choose what the student wants to communicate."
            textSize = 16f; setPadding(0, 8, 0, 16)
        })
        val grid = android.widget.GridLayout(this@MainActivity).apply { columnCount = 2; useDefaultMargins = true }
        listOf("Play", "Break", "Help", "More", "All done", "Yes", "No", "I don't know").forEach { choice ->
            grid.addView(Button(this@MainActivity).apply {
                text = choice; textSize = 19f; minHeight = 64
                setOnClickListener {
                    supportPrefs().edit().putInt("choice_selections", supportPrefs().getInt("choice_selections", 0) + 1).apply()
                    speakCommunicationText(choice)
                }
            })
        }
        list.addView(grid)
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showQuickCommunication() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Quick Communication"; textSize = 24f; setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "One tap can communicate a common need."
            textSize = 16f; setPadding(0, 8, 0, 16)
        })
        listOf(
            "I need help", "I need a break", "I am finished", "Please wait",
            "I want more", "I want to stop", "Yes", "No", "I don't know"
        ).forEach { phrase ->
            list.addView(Button(this@MainActivity).apply {
                text = phrase; textSize = 18f; minHeight = 56
                setOnClickListener {
                    addSavedPhrase(phrase)
                    speakCommunicationText(phrase)
                }
            })
        }
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showVisualProgress() {
        val recordings = File(filesDir, "dialogue_history").listFiles()?.count { it.isDirectory } ?: 0
        val wordCount = loadStudentWordBank().let { studentWordBank.size }
        val phraseCount = loadSavedPhrases().size
        val favoriteCount = favoritePhrases().size
        val practice = supportPrefs().getInt("practice_attempts", 0)
        val choices = supportPrefs().getInt("choice_selections", 0)

        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(28, 20, 28, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Visual Progress"; textSize = 24f; setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        val grid = android.widget.GridLayout(this@MainActivity).apply { columnCount = 2; useDefaultMargins = true }
        val stats = listOf(
            "🎙️ Saved recordings" to recordings,
            "🗣️ Recorded words" to wordCount,
            "⭐ Favorite phrases" to favoriteCount,
            "💬 Saved phrases" to phraseCount,
            "🔁 Practice tries" to practice,
            "☑️ Choices made" to choices
        )
        stats.forEach { (label, value) ->
            grid.addView(TextView(this@MainActivity).apply {
                text = "$label\n$value"; textSize = 18f; minHeight = 90
                setPadding(12, 12, 12, 12)
                setBackgroundColor(0xFFEFF4F8.toInt())
            })
        }
        list.addView(grid)
        list.addView(TextView(this@MainActivity).apply {
            text = "These are activity counts, not measures of speech quality or a diagnosis."
            textSize = 14f; setPadding(0, 18, 0, 8)
        })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showSupportNotes() {
        val prefs = supportPrefs()
        val note = EditText(this@MainActivity).apply {
            hint = "What supports communication today? Favorite prompts, choices, routines, etc."
            minLines = 6; gravity = android.view.Gravity.TOP
            setText(prefs.getString("caregiver_notes", ""))
        }
        android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Teacher / Caregiver Notes")
            .setView(note)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Save") { _, _ ->
                prefs.edit().putString("caregiver_notes", note.text.toString()).apply()
                Toast.makeText(this@MainActivity, "Notes saved on this device.", Toast.LENGTH_SHORT).show()
            }.create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
    }

    private fun showCustomVocabulary() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Custom Vocabulary"; textSize = 24f; setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        val input = EditText(this@MainActivity).apply { hint = "Add a word"; isSingleLine = true; textSize = 18f }
        list.addView(input)
        val items = loadCustomVocabulary()
        val itemsView = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.VERTICAL }
        list.addView(itemsView)

        fun render() {
            itemsView.removeAllViews()
            if (items.isEmpty()) {
                itemsView.addView(TextView(this@MainActivity).apply { text = "No custom words yet."; setPadding(0, 12, 0, 12) })
            }
            items.toList().forEach { word ->
                val row = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.HORIZONTAL }
                row.addView(TextView(this@MainActivity).apply {
                    text = word; textSize = 18f
                    layoutParams = LinearLayout.LayoutParams(0, -2, 1f)
                })
                row.addView(Button(this@MainActivity).apply {
                    text = "Delete"
                    setOnClickListener { items.remove(word); saveCustomVocabulary(items); render() }
                })
                itemsView.addView(row)
            }
        }
        list.addView(Button(this@MainActivity).apply {
            text = "Add Word"
            setOnClickListener {
                val w = input.text.toString().trim()
                if (w.isNotBlank() && w.length <= 40) {
                    items.add(w); saveCustomVocabulary(items); input.text.clear(); render()
                }
            }
        })
        render()
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showPrivacyControls() {
        val prefs = getPreferences(MODE_PRIVATE)
        val offline = prefs.getBoolean("offline_mode", false)
        val message = TextView(this@MainActivity).apply {
            text = "Recordings, word-bank audio, phrases, profile data, and notes are stored locally by default. Analysis requires sending a recording to the configured server unless Offline Mode is enabled.\n\nCurrent Offline Mode: ${if (offline) "ON" else "OFF"}"
            textSize = 16f; setPadding(4, 4, 4, 12)
        }
        val builder = android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Privacy & Offline")
            .setView(message)
            .setPositiveButton(if (offline) "Turn Offline Mode Off" else "Turn Offline Mode On") { _, _ ->
                prefs.edit().putBoolean("offline_mode", !offline).apply()
                Toast.makeText(this@MainActivity, "Offline Mode is now ${if (!offline) "ON" else "OFF"}.", Toast.LENGTH_SHORT).show()
            }
            .setNeutralButton("Delete Local Student Data") { _, _ ->
                android.app.AlertDialog.Builder(this@MainActivity)
                    .setTitle("Delete local student data?")
                    .setMessage("This removes saved recordings, word-bank audio, phrases, favorites, custom vocabulary, notes, and live-session summaries from this device.")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Delete") { _, _ -> deleteAllLocalStudentData() }
                    .create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
            }
            .setNegativeButton("Close", null)
        builder.create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
    }

    private fun deleteAllLocalStudentData() {
        listOf(
            "dialogue_history", "student_word_bank", "live_session_summaries",
            "saved_phrases.json", "custom_vocabulary.json"
        ).forEach { File(filesDir, it).let { f -> if (f.exists()) f.deleteRecursively() } }
        supportPrefs().edit().clear().apply()
        studentWordBank.clear()
        Toast.makeText(this@MainActivity, "Local student data deleted.", Toast.LENGTH_LONG).show()
    }

    private fun speakCommunicationText(text: String) {
        val clean = text.trim()
        if (clean.isBlank()) return

        // Prefer a single student recording when this is one word.
        if (!clean.contains(" ")) {
            if (playStudentWord(clean)) return
        }
        tts?.let {
            it.speak(clean, TextToSpeech.QUEUE_FLUSH, null, "communication")
            return
        }
        tts = TextToSpeech(this@MainActivity) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.speak(clean, TextToSpeech.QUEUE_FLUSH, null, "communication")
            }
        }
    }

    private fun showCommunicationModes() {
        val prefs = supportPrefs()
        val current = prefs.getString("communication_mode", "Multi-modal") ?: "Multi-modal"
        val modes = arrayOf(
            "Multi-modal", "Recorded Student Voice", "Visual / Picture",
            "Text", "Android Voice", "Speech + Suggestions"
        )
        val selected = modes.indexOf(current).coerceAtLeast(0)
        android.app.AlertDialog.Builder(this@MainActivity)
            .setTitle("Communication Mode")
            .setSingleChoiceItems(modes, selected) { dialog, which ->
                prefs.edit().putString("communication_mode", modes[which]).apply()
                Toast.makeText(this@MainActivity, "Mode: ${modes[which]}", Toast.LENGTH_SHORT).show()
                dialog.dismiss()
            }
            .setNegativeButton("Close", null)
            .create().also { alert -> alert.setOnShowListener { styleUnifiedDialog(alert) }; alert.show() }
    }


    // ---------- Communication interpretation supports ----------

    private fun interpretationPrefs() =
        getSharedPreferences("communication_interpretation", MODE_PRIVATE)

    private fun readJsonArray(fileName: String): JSONArray {
        val f = File(filesDir, fileName)
        return try {
            if (f.exists()) JSONArray(f.readText()) else JSONArray()
        } catch (_: Exception) { JSONArray() }
    }

    private fun writeJsonArray(fileName: String, a: JSONArray) {
        File(filesDir, fileName).writeText(a.toString())
    }

    private fun showCommunicationInterpretationTools() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(popupDp(22), popupDp(18), popupDp(22), popupDp(22))
        }

        list.addView(popupHeader(
            "Communication Interpretation Tools",
            "Explore possible meanings while keeping uncertainty visible.",
            "🧠"
        ))

        fun addTool(icon: String, title: String, description: String, action: () -> Unit) {
            list.addView(popupActionButton(title, description, icon) {
                dialog.dismiss()
                action()
            })
        }

        addTool("🔎", "Context-Aware Interpretation", "Use the current activity to narrow possible meanings.") { showContextAwareInterpretation() }
        addTool("🗣️", "Personal Pronunciation Profile", "View descriptive sound patterns for this student.") { showPersonalPronunciationProfile() }
        addTool("📊", "Sound-Pattern History", "Review possible omissions and substitutions over time.") { showSoundPatternHistory() }
        addTool("🔤", "Multiple Candidate Meanings", "Compare several possible words instead of one forced answer.") { showCandidateMeanings() }
        addTool("🧩", "Context + Sound Matching", "Combine context, word bank, and sound clues.") { showContextSoundMatching() }
        addTool("✅", "Caregiver Confirmation", "Confirm what the student intended and build their dictionary.") { showCaregiverConfirmation() }
        addTool("📖", "Communication History", "Review successful communication attempts.") { showCommunicationHistory() }
        addTool("🖼️", "Picture Candidate Results", "Show visual candidates the student can select.") { showPictureCandidates() }
        addTool("👋", "Gesture / Speech Notes", "Record gestures and context that accompanied speech.") { showGestureNotes() }
        addTool("🎓", "Personalized Learning", "Use explicitly confirmed meanings from this student.") { showPersonalizedLearning() }
        addTool("❓", "I'm Not Sure Yet", "Use a safe fallback when no interpretation is reliable.") { showNotSureMode() }

        list.addView(popupInfoCard(
            "Tip",
            "Try more than one tool when the meaning is unclear. Different evidence can point toward different possibilities.",
            "✨"
        ))
        list.addView(popupActionButton("Close", null, "×") { dialog.dismiss() })

        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showContextAwareInterpretation() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Context-Aware Interpretation"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })

        val contextInput = EditText(this@MainActivity).apply {
            hint = "Context: lunch, playground, classroom..."
            textSize = 17f
        }
        val speechInput = EditText(this@MainActivity).apply {
            hint = "What was heard?"
            textSize = 17f
        }
        val results = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.VERTICAL }

        list.addView(contextInput)
        list.addView(speechInput)
        list.addView(Button(this@MainActivity).apply {
            text = "Find Possible Meanings"
            setOnClickListener {
                results.removeAllViews()
                val context = contextInput.text.toString().trim().lowercase()
                val heard = speechInput.text.toString().trim().lowercase()
                val contextWords = when {
                    context.contains("lunch") || context.contains("eat") ->
                        listOf("food", "eat", "drink", "more", "apple", "juice", "water")
                    context.contains("play") || context.contains("playground") ->
                        listOf("play", "ball", "swing", "slide", "outside", "more")
                    context.contains("school") || context.contains("class") ->
                        listOf("teacher", "help", "break", "book", "pencil", "bathroom")
                    context.contains("home") ->
                        listOf("mom", "dad", "home", "food", "bathroom", "bed")
                    else -> (loadCustomVocabulary() + studentWordBank.keys +
                            listOf("help", "more", "stop", "play", "eat", "drink", "bathroom")).distinct()
                }
                val candidates = contextWords.filter {
                    heard.isBlank() || it.startsWith(heard.take(2)) || it.contains(heard.take(2))
                }.take(6)
                val finalList = if (candidates.isEmpty()) contextWords.take(6) else candidates
                results.addView(TextView(this@MainActivity).apply {
                    text = "Possible matches — confirm with the student:"
                    textSize = 16f; setPadding(0, 12, 0, 8)
                })
                finalList.forEach { word ->
                    results.addView(Button(this@MainActivity).apply {
                        text = word; textSize = 18f
                        setOnClickListener { recordInterpretation(heard, word, context, "context"); speakCommunicationText(word) }
                    })
                }
            }
        })
        list.addView(results)
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showPersonalPronunciationProfile() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(28, 20, 28, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Personal Pronunciation Profile"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })

        val history = readJsonArray("communication_interpretation_history.json")
        val counts = linkedMapOf<String, Int>()
        for (i in 0 until history.length()) {
            val o = history.optJSONObject(i) ?: continue
            val note = o.optString("sound_pattern")
            if (note.isNotBlank()) counts[note] = (counts[note] ?: 0) + 1
        }

        if (counts.isEmpty()) {
            list.addView(TextView(this@MainActivity).apply {
                text = "No confirmed speech-pattern observations yet.\n\nAs caregivers confirm examples, the app can build a descriptive profile."
                textSize = 17f; setPadding(0, 16, 0, 16)
            })
        } else {
            counts.entries.sortedByDescending { it.value }.forEach { (pattern, n) ->
                list.addView(TextView(this@MainActivity).apply {
                    text = "• $pattern — $n observation(s)"
                    textSize = 18f; setPadding(0, 8, 0, 8)
                })
            }
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "This is an observational communication aid, not a speech-language or diagnostic assessment."
            textSize = 14f; setPadding(0, 18, 0, 0)
        })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showSoundPatternHistory() {
        val history = readJsonArray("communication_interpretation_history.json")
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Sound-Pattern History"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        if (history.length() == 0) {
            list.addView(TextView(this@MainActivity).apply {
                text = "No observations have been confirmed yet."; textSize = 17f
            })
        }
        for (i in (history.length() - 1) downTo 0) {
            val o = history.optJSONObject(i) ?: continue
            list.addView(TextView(this@MainActivity).apply {
                text = "${o.optString("heard")} → ${o.optString("meaning")}\nContext: ${o.optString("context")}\nPattern: ${o.optString("sound_pattern")}"
                textSize = 16f
                setPadding(0, 10, 0, 10)
            })
        }
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showCandidateMeanings() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        val heard = EditText(this@MainActivity).apply { hint = "Speech attempt"; textSize = 18f }
        val candidates = EditText(this@MainActivity).apply {
            hint = "Possible words, separated by commas"; textSize = 18f
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Multiple Candidate Meanings"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "The app will present possibilities rather than claiming one is correct."
            textSize = 16f; setPadding(0, 8, 0, 14)
        })
        list.addView(heard); list.addView(candidates)
        val grid = android.widget.GridLayout(this@MainActivity).apply { columnCount = 2; useDefaultMargins = true }
        list.addView(Button(this@MainActivity).apply {
            text = "Show Choices"
            setOnClickListener {
                grid.removeAllViews()
                candidates.text.toString().split(",").map { it.trim() }.filter { it.isNotBlank() }.take(8).forEach { word ->
                    grid.addView(Button(this@MainActivity).apply {
                        text = word; textSize = 18f; minHeight = 64
                        setOnClickListener {
                            recordInterpretation(heard.text.toString(), word, "", "candidate")
                            speakCommunicationText(word)
                        }
                    })
                }
            }
        })
        list.addView(grid)
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showContextSoundMatching() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        val heard = EditText(this@MainActivity).apply { hint = "What was heard?" }
        val context = EditText(this@MainActivity).apply { hint = "Context / activity" }
        val results = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.VERTICAL }
        list.addView(TextView(this@MainActivity).apply {
            text = "Context + Sound Matching"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(heard); list.addView(context)
        list.addView(Button(this@MainActivity).apply {
            text = "Generate Possibilities"
            setOnClickListener {
                results.removeAllViews()
                val base = (loadCustomVocabulary() + studentWordBank.keys +
                        listOf("help","more","stop","play","eat","drink","water","bathroom","break","outside","home","mom","dad")).distinct()
                val h = heard.text.toString().trim().lowercase()
                val c = context.text.toString().trim().lowercase()
                val ranked = base.map { w ->
                    var score = 0
                    if (h.isNotBlank() && (w.startsWith(h.take(1)) || w.contains(h.take(1)))) score += 2
                    if (c.isNotBlank() && (
                        (c.contains("eat") && w in listOf("eat","food","drink","water","more")) ||
                        (c.contains("play") && w in listOf("play","ball","outside","more")) ||
                        (c.contains("school") && w in listOf("teacher","help","break","bathroom"))
                    )) score += 4
                    w to score
                }.sortedByDescending { it.second }.take(6)
                ranked.forEach { (word, score) ->
                    results.addView(Button(this@MainActivity).apply {
                        text = "$word  •  context/sound match: $score"
                        textSize = 17f
                        setOnClickListener {
                            recordInterpretation(h, word, c, "context+sound")
                            speakCommunicationText(word)
                        }
                    })
                }
            }
        })
        list.addView(results)
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showCaregiverConfirmation() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        val heard = EditText(this@MainActivity).apply { hint = "What the app heard" }
        val meaning = EditText(this@MainActivity).apply { hint = "What the student meant" }
        val pattern = EditText(this@MainActivity).apply {
            hint = "Optional observation: initial /k/ may be omitted, /s/→/t/, etc."
        }
        val context = EditText(this@MainActivity).apply { hint = "Context (optional)" }
        list.addView(TextView(this@MainActivity).apply {
            text = "Caregiver Confirmation"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "Use this only when the student or caregiver can confirm the intended meaning."
            textSize = 16f; setPadding(0, 8, 0, 14)
        })
        list.addView(heard); list.addView(meaning); list.addView(pattern); list.addView(context)
        list.addView(Button(this@MainActivity).apply {
            text = "✓ Confirm Meaning"
            setOnClickListener {
                val h = heard.text.toString().trim()
                val m = meaning.text.toString().trim()
                if (m.isNotBlank()) {
                    recordInterpretation(h, m, context.text.toString(), "caregiver-confirmed", pattern.text.toString())
                    recordConfirmedMeaningForLearning(h, m, context.text.toString())
                    addSavedPhrase(m)
                    Toast.makeText(this@MainActivity, "Confirmed meaning saved locally.", Toast.LENGTH_SHORT).show()
                    dialog.dismiss()
                }
            }
        })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun recordInterpretation(
        heard: String,
        meaning: String,
        context: String,
        source: String,
        soundPattern: String = ""
    ) {
        val a = readJsonArray("communication_interpretation_history.json")
        val o = JSONObject()
        o.put("timestamp", System.currentTimeMillis())
        o.put("heard", heard)
        o.put("meaning", meaning)
        o.put("context", context)
        o.put("source", source)
        o.put("sound_pattern", soundPattern.ifBlank {
            if (heard.isNotBlank() && meaning.isNotBlank() &&
                meaning.first().lowercaseChar() != heard.first().lowercaseChar()
            ) "Possible initial-sound difference" else "No confirmed sound-pattern note"
        })
        a.put(o)
        // Bound local history.
        while (a.length() > 500) a.remove(0)
        writeJsonArray("communication_interpretation_history.json", a)
    }

    private fun showCommunicationHistory() {
        val history = readJsonArray("communication_interpretation_history.json")
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Communication History"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        if (history.length() == 0) {
            list.addView(TextView(this@MainActivity).apply {
                text = "No confirmed communication attempts yet."; textSize = 17f
            })
        }
        for (i in (history.length() - 1) downTo 0) {
            val o = history.optJSONObject(i) ?: continue
            val source = o.optString("source")
            list.addView(TextView(this@MainActivity).apply {
                text = "Heard: ${o.optString("heard")}\nMeaning: ${o.optString("meaning")}\nContext: ${o.optString("context")}\nSource: $source"
                textSize = 16f; setPadding(0, 10, 0, 10)
            })
        }
        list.addView(Button(this@MainActivity).apply {
            text = "Delete History"
            setOnClickListener {
                File(filesDir, "communication_interpretation_history.json").delete()
                dialog.dismiss()
            }
        })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showPictureCandidates() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Picture Candidate Results"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "Visual symbols are simple supports, not a claim about what the student means."
            textSize = 16f; setPadding(0, 8, 0, 14)
        })
        val candidates = listOf(
            "🍎" to "apple", "🍪" to "snack", "💧" to "water", "🥤" to "drink",
            "⚽" to "ball", "🧸" to "play", "🚽" to "bathroom", "🛝" to "outside",
            "🙋" to "help", "🛑" to "stop", "🛌" to "break", "🏠" to "home"
        )
        val grid = android.widget.GridLayout(this@MainActivity).apply { columnCount = 3; useDefaultMargins = true }
        candidates.forEach { (emoji, word) ->
            grid.addView(Button(this@MainActivity).apply {
                text = "$emoji\n$word"; textSize = 18f; minHeight = 88
                setOnClickListener {
                    recordInterpretation("", word, "", "picture-selected")
                    speakCommunicationText(word)
                    Toast.makeText(this@MainActivity, "Selected: $word", Toast.LENGTH_SHORT).show()
                }
            })
        }
        list.addView(grid)
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showGestureNotes() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(24, 20, 24, 24)
        }
        val context = EditText(this@MainActivity).apply { hint = "What was happening?" }
        val gesture = EditText(this@MainActivity).apply {
            hint = "Gesture / action: pointed, reached, looked at object, signed, etc."
            minLines = 3; gravity = android.view.Gravity.TOP
        }
        val speech = EditText(this@MainActivity).apply { hint = "Speech attempt (optional)" }
        list.addView(TextView(this@MainActivity).apply {
            text = "Gesture / Speech Notes"; textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "Non-speech behavior can provide useful context when speech is unclear."
            textSize = 16f; setPadding(0, 8, 0, 14)
        })
        list.addView(context); list.addView(gesture); list.addView(speech)
        list.addView(Button(this@MainActivity).apply {
            text = "Save Observation"
            setOnClickListener {
                val a = readJsonArray("gesture_observations.json")
                val o = JSONObject()
                o.put("timestamp", System.currentTimeMillis())
                o.put("context", context.text.toString())
                o.put("gesture", gesture.text.toString())
                o.put("speech", speech.text.toString())
                a.put(o)
                while (a.length() > 500) a.remove(0)
                writeJsonArray("gesture_observations.json", a)
                Toast.makeText(this@MainActivity, "Observation saved locally.", Toast.LENGTH_SHORT).show()
                dialog.dismiss()
            }
        })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showNotSureMode() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL; setPadding(28, 24, 28, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "I'm Not Sure Yet"; textSize = 26f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "It's okay not to have an interpretation. Let the student show you another way."
            textSize = 18f; setPadding(0, 12, 0, 20)
        })
        listOf(
            "🖼️ Show pictures" to { showPictureCandidates() },
            "🧩 Build a sentence" to { showVisualSentenceBuilder() },
            "☑️ Offer choices" to { showChoiceBoard() },
            "✍️ Ask the student to type / select" to { showCandidateMeanings() }
        ).forEach { (label, action) ->
            list.addView(Button(this@MainActivity).apply {
                text = label; textSize = 18f; minHeight = 60
                setOnClickListener { dialog.dismiss(); action() }
            })
        }
        list.addView(Button(this@MainActivity).apply {
            text = "Record as Unresolved"
            setOnClickListener {
                val a = readJsonArray("communication_interpretation_history.json")
                val o = JSONObject()
                o.put("timestamp", System.currentTimeMillis())
                o.put("heard", "")
                o.put("meaning", "Unresolved")
                o.put("context", "")
                o.put("source", "not-sure")
                o.put("sound_pattern", "")
                a.put(o)
                while (a.length() > 500) a.remove(0)
                writeJsonArray("communication_interpretation_history.json", a)
                Toast.makeText(this@MainActivity, "Marked unresolved.", Toast.LENGTH_SHORT).show()
                dialog.dismiss()
            }
        })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }


    private fun learningFile(): File = File(filesDir, "personalized_communication_map.json")

    private fun loadLearningMap(): JSONArray = try {
        val f = learningFile()
        if (f.exists()) JSONArray(f.readText()) else JSONArray()
    } catch (_: Exception) { JSONArray() }

    private fun saveLearningMap(a: JSONArray) {
        while (a.length() > 1000) a.remove(0)
        learningFile().writeText(a.toString())
    }

    private fun recordConfirmedMeaningForLearning(heard: String, meaning: String, context: String) {
        val h = heard.trim().lowercase()
        val m = meaning.trim().lowercase()
        val c = context.trim().lowercase()
        if (h.isBlank() || m.isBlank()) return
        val a = loadLearningMap()
        var found = false
        for (i in 0 until a.length()) {
            val o = a.optJSONObject(i) ?: continue
            if (o.optString("heard") == h && o.optString("meaning") == m && o.optString("context") == c) {
                o.put("confirmations", o.optInt("confirmations", 0) + 1)
                o.put("lastConfirmed", System.currentTimeMillis())
                found = true
                break
            }
        }
        if (!found) {
            a.put(JSONObject().apply {
                put("heard", h)
                put("meaning", m)
                put("context", c)
                put("confirmations", 1)
                put("lastConfirmed", System.currentTimeMillis())
            })
        }
        saveLearningMap(a)
    }

    private fun personalizedCandidates(heard: String, context: String): List<Pair<String, Int>> {
        val h = heard.trim().lowercase()
        val c = context.trim().lowercase()
        val a = loadLearningMap()
        val scores = mutableMapOf<String, Int>()
        for (i in 0 until a.length()) {
            val o = a.optJSONObject(i) ?: continue
            val oh = o.optString("heard")
            val m = o.optString("meaning")
            val oc = o.optString("context")
            if (m.isBlank()) continue
            var score = o.optInt("confirmations", 1) * 3
            if (h.isNotBlank() && oh == h) score += 12
            else if (h.isNotBlank() && (oh.contains(h) || h.contains(oh))) score += 5
            if (c.isNotBlank() && oc.isNotBlank() && (oc.contains(c) || c.contains(oc))) score += 6
            scores[m] = maxOf(scores[m] ?: 0, score)
        }
        return scores.entries.sortedByDescending { it.value }.take(8).map { it.key to it.value }
    }

    private fun showPersonalizedLearning() {
        val dialog = android.app.Dialog(this@MainActivity)
        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 20, 24, 24)
        }
        list.addView(TextView(this@MainActivity).apply {
            text = "Personalized Communication Learning"
            textSize = 24f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        })
        list.addView(TextView(this@MainActivity).apply {
            text = "Only meanings explicitly confirmed by the student or caregiver are learned."
            textSize = 16f
            setPadding(0, 8, 0, 14)
        })
        val heard = EditText(this@MainActivity).apply { hint = "What was heard?" }
        val context = EditText(this@MainActivity).apply { hint = "Context (optional)" }
        val results = LinearLayout(this@MainActivity).apply { orientation = LinearLayout.VERTICAL }
        list.addView(heard)
        list.addView(context)
        list.addView(Button(this@MainActivity).apply {
            text = "Show Personal Matches"
            setOnClickListener {
                results.removeAllViews()
                val matches = personalizedCandidates(heard.text.toString(), context.text.toString())
                if (matches.isEmpty()) {
                    results.addView(TextView(this@MainActivity).apply {
                        text = "No confirmed personal matches yet."
                        textSize = 17f
                    })
                }
                matches.forEach { (word, score) ->
                    results.addView(Button(this@MainActivity).apply {
                        text = "$word  • personal match $score"
                        textSize = 17f
                        setOnClickListener { speakCommunicationText(word) }
                    })
                }
            }
        })
        list.addView(results)
        list.addView(Button(this@MainActivity).apply {
            text = "Clear Personal Learning"
            setOnClickListener {
                learningFile().delete()
                results.removeAllViews()
                Toast.makeText(this@MainActivity, "Personal learning cleared.", Toast.LENGTH_SHORT).show()
            }
        })
        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

    private fun showCaregiverSetupAndReadiness() {
        val prefs = getSharedPreferences("caregiver_setup", MODE_PRIVATE)
        val acknowledged = prefs.getBoolean("privacy_ack", false)
        val complete = prefs.getBoolean("setup_complete", false)
        val dialog = android.app.Dialog(this@MainActivity)

        val list = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(popupDp(22), popupDp(18), popupDp(22), popupDp(22))
        }

        list.addView(popupHeader(
            "Caregiver Setup & Pilot Readiness",
            "Review privacy, personalized learning, and the pilot checklist before regular use.",
            "🛡️"
        ))

        val statusCard = popupInfoCard(
            "Setup status",
            "Privacy acknowledgement: ${if (acknowledged) "complete ✓" else "needed !"}\nCaregiver setup: ${if (complete) "complete ✓" else "needed !"}",
            if (acknowledged && complete) "✅" else "⚠️"
        )
        list.addView(statusCard)

        fun refreshStatus() {
            val a = prefs.getBoolean("privacy_ack", false)
            val c = prefs.getBoolean("setup_complete", false)
            val body = statusCard.getChildAt(1) as? TextView
            body?.text = "Privacy acknowledgement: ${if (a) "complete ✓" else "needed !"}\nCaregiver setup: ${if (c) "complete ✓" else "needed !"}"
        }

        list.addView(popupActionButton(
            "Review Privacy & Recording Notice",
            "Review how recordings and student information should be handled.",
            "📄",
            true
        ) {
            val privacy = android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Privacy & Recording Notice")
                .setMessage("Voice recordings and student information can be sensitive. Keep data local when possible. Only use network features that the caregiver/guardian and your organization have authorized. This app is a communication-support tool, not a diagnosis or clinical assessment.")
                .setNegativeButton("Not now", null)
                .setPositiveButton("I understand") { _, _ ->
                    prefs.edit().putBoolean("privacy_ack", true).apply()
                    refreshStatus()
                }
                .create()
            privacy.setOnShowListener { styleUnifiedDialog(privacy) }
            privacy.show()
        })

        list.addView(popupActionButton(
            "Open Personalized Learning",
            "Review confirmed meanings and student-specific learning.",
            "🎓"
        ) {
            dialog.dismiss()
            showPersonalizedLearning()
        })

        list.addView(popupActionButton(
            "Mark Setup Complete",
            "Finish caregiver setup after reviewing the privacy notice.",
            "✓"
        ) {
            if (!prefs.getBoolean("privacy_ack", false)) {
                Toast.makeText(this@MainActivity, "Review the privacy notice first.", Toast.LENGTH_SHORT).show()
            } else {
                prefs.edit().putBoolean("setup_complete", true).apply()
                refreshStatus()
            }
        })

        list.addView(popupInfoCard(
            "Pilot checklist",
            "✓ Test with familiar routines.\n✓ Confirm meanings rather than assuming them.\n✓ Use pictures/choices when speech is uncertain.\n✓ Test Offline Mode.\n✓ Keep student information out of GitHub.",
            "📋"
        ).apply {
            val lp = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
            lp.setMargins(0, popupDp(10), 0, 0)
            layoutParams = lp
        })

        list.addView(popupActionButton("Close", null, "×") { dialog.dismiss() })

        dialog.setContentView(ScrollView(this@MainActivity).apply { addView(list) })
        dialog.show()
        styleUnifiedDialog(dialog)
    }

}