#!/usr/bin/env python3
"""Patch existing Fynn1 Android sources in CI; never replace the entire project."""
from pathlib import Path

layout = Path('app/src/main/res/layout/activity_main.xml')
activity = Path('app/src/main/java/com/firstsoundhelper/MainActivity.kt')
for path in (layout, activity):
    if not path.is_file():
        raise SystemExit(f'ERROR: Missing expected source file: {path}')

xml = layout.read_text(encoding='utf-8')
kt = activity.read_text(encoding='utf-8')

def once_replace(text, needle, replacement, label):
    n = text.count(needle)
    if n != 1:
        raise SystemExit(f'ERROR: Expected exactly one {label}; found {n}. Stopping to avoid damaging source.')
    return text.replace(needle, replacement, 1)

if 'activeRecordingIndicator' not in xml:
    indicator = '''<TextView
    android:id="@+id/activeRecordingIndicator"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:text="● Not Recording · INDICATOR V2"
    android:textColor="#555555"
    android:textStyle="bold"
    android:textSize="17sp"
    android:gravity="center"
    android:paddingTop="12dp"
    android:paddingBottom="12dp"
    android:visibility="visible" />
'''
    xml = once_replace(xml, '<Button android:id="@+id/stopButton"', indicator + '<Button android:id="@+id/stopButton"', 'Stop button layout')

if 'private fun setRecordingIndicator(active: Boolean)' not in kt:
    kt = once_replace(kt, 'import android.widget.EditText', 'import android.animation.ObjectAnimator\nimport android.animation.ValueAnimator\nimport android.widget.EditText', 'EditText import')
    kt = once_replace(kt, '    private var recording = false', '    private var recording = false\n    private var recordingIndicatorAnimator: ObjectAnimator? = null', 'recording field')
    method = '''    private fun setRecordingIndicator(active: Boolean) {
        val indicator = findViewById<TextView>(R.id.activeRecordingIndicator)
        recordingIndicatorAnimator?.cancel()
        recordingIndicatorAnimator = null
        indicator.alpha = 1f
        indicator.visibility = android.view.View.VISIBLE
        if (active) {
            indicator.text = "● RECORDING — Microphone Active"
            indicator.setTextColor(Color.RED)
            recordingIndicatorAnimator = ObjectAnimator.ofFloat(indicator, "alpha", 1f, 0.25f, 1f).apply {
                duration = 900L
                repeatCount = ValueAnimator.INFINITE
                start()
            }
        } else {
            indicator.text = "● Not Recording · INDICATOR V2"
            indicator.setTextColor(Color.DKGRAY)
        }
    }

'''
    kt = once_replace(kt, '    private fun startRecording() {', method + '    private fun startRecording() {', 'startRecording method')
    kt = once_replace(kt, 'pcm.reset(); recording=true', 'pcm.reset(); recording=true\n        setRecordingIndicator(true)', 'recording start assignment')
    kt = once_replace(kt, '    private fun stopRecording() {\n        recording=false', '    private fun stopRecording() {\n        recording=false\n        setRecordingIndicator(false)', 'stopRecording method')
    kt = once_replace(kt, 'super.onCreate(b); setContentView(R.layout.activity_main)', 'super.onCreate(b); setContentView(R.layout.activity_main)\n        setRecordingIndicator(false)', 'onCreate layout setup')

assert 'activeRecordingIndicator' in xml
assert 'setRecordingIndicator(true)' in kt
assert 'setRecordingIndicator(false)' in kt
layout.write_text(xml, encoding='utf-8')
activity.write_text(kt, encoding='utf-8')
print('SUCCESS: Recording indicator source patched and verified.')
