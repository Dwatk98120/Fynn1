package com.firstsoundhelper

import android.app.AlertDialog
import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/** Dedicated stacked actions avoid OEM horizontal AlertDialog button clipping. */
internal object LocalAudioRemovalDialog {
    fun create(context: Context, count: Int, onConfirm: () -> Unit): AlertDialog {
        fun dp(value: Int) = (value * context.resources.displayMetrics.density).toInt()
        fun rounded(color: String) = GradientDrawable().apply {
            setColor(Color.parseColor(color)); cornerRadius = dp(16).toFloat()
        }
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(20), dp(20), dp(20))
            background = rounded("#FFFFFF")
        }
        val title = TextView(context).apply {
            text = "Remove local audio?"; textSize = 22f
            setTextColor(Color.parseColor("#21124D")); setTypeface(typeface, Typeface.BOLD)
        }
        val message = TextView(context).apply {
            text = "The Parent PC verified $count matching saved recording(s).\n\n" +
                "Remove only their audio from this phone?\n\n" +
                "Metadata, labels, analysis and audit history stay here. PC originals are retained. " +
                "Each PC copy will be checked again immediately before removal."
            textSize = 16f; setTextColor(Color.parseColor("#4B4855"))
            setPadding(0, dp(14), 0, dp(14))
        }
        val content = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            addView(title, LinearLayout.LayoutParams(-1, -2))
            addView(message, LinearLayout.LayoutParams(-1, -2))
        }
        root.addView(ScrollView(context).apply { addView(content) }, LinearLayout.LayoutParams(-1, 0, 1f))
        fun action(label: String, actionTag: String, color: String, textColor: String) = Button(context).apply {
            text = label; tag = actionTag; isAllCaps = false; textSize = 16f
            setSingleLine(false); maxLines = Int.MAX_VALUE; ellipsize = null
            minHeight = dp(56); minimumWidth = 0
            setPadding(dp(16), dp(10), dp(16), dp(10))
            setTextColor(Color.parseColor(textColor)); background = rounded(color)
            backgroundTintList = ColorStateList.valueOf(Color.parseColor(color))
            setTypeface(typeface, Typeface.BOLD)
        }
        val remove = action("Remove local audio", "local_audio_remove", "#6D4DB3", "#FFFFFF")
        val keep = action("Keep local audio", "local_audio_keep", "#F3F1F6", "#4B4855")
        root.addView(remove, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) })
        root.addView(keep, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) })
        val dialog = AlertDialog.Builder(context).setView(root, 0, 0, 0, 0).create()
        remove.setOnClickListener {
            if (!remove.isEnabled) return@setOnClickListener
            remove.isEnabled = false
            try { onConfirm() } finally { dialog.dismiss() }
        }
        keep.setOnClickListener { dialog.cancel() }
        dialog.setOnShowListener {
            dialog.window?.apply {
                setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
                val metrics = context.resources.displayMetrics
                setLayout((metrics.widthPixels * 0.91f).toInt(), (metrics.heightPixels * 0.85f).toInt())
            }
            keep.requestFocus()
        }
        return dialog
    }
}
