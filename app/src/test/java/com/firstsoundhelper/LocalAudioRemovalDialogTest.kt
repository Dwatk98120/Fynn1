package com.firstsoundhelper

import android.app.Activity
import android.graphics.Rect
import android.view.View
import android.widget.Button
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowLooper

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], manifest = Config.NONE)
class LocalAudioRemovalDialogTest {
    private fun checkLayout(width: Int, height: Int, font: Float) {
        val orientation = if (width > height) "land" else "port"
        RuntimeEnvironment.setQualifiers("w${width}dp-h${height}dp-$orientation-mdpi")
        RuntimeEnvironment.setFontScale(font)
        val activity = Robolectric.buildActivity(Activity::class.java).setup().get()
        assertEquals(width, activity.resources.displayMetrics.widthPixels)
        assertEquals(font, activity.resources.configuration.fontScale, 0.001f)
        var confirmations = 0
        val dialog = LocalAudioRemovalDialog.create(activity, 1) { confirmations++ }
        dialog.show()
        ShadowLooper.idleMainLooper()
        val decor = dialog.window!!.decorView
        val attributes = dialog.window!!.attributes
        decor.measure(View.MeasureSpec.makeMeasureSpec(attributes.width, View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(attributes.height, View.MeasureSpec.EXACTLY))
        decor.layout(0, 0, attributes.width, attributes.height)
        val remove = decor.findViewWithTag<Button>("local_audio_remove")
        val keep = decor.findViewWithTag<Button>("local_audio_keep")
        val removeRect = Rect(); val keepRect = Rect()
        assertTrue("Removal action must be visible", remove.getGlobalVisibleRect(removeRect))
        assertTrue("Keep action must be visible", keep.getGlobalVisibleRect(keepRect))
        assertEquals("Removal must not be vertically clipped", remove.height, removeRect.height())
        assertEquals("Keep must not be vertically clipped", keep.height, keepRect.height())
        assertEquals("Removal must not be horizontally clipped", remove.width, removeRect.width())
        assertTrue("Actions must stack without overlap", removeRect.bottom <= keepRect.top)
        assertTrue(remove.height >= 48 && keep.height >= 48)
        for (button in listOf(remove, keep)) {
            for (line in 0 until button.layout.lineCount) assertEquals(0, button.layout.getEllipsisCount(line))
            assertEquals(button.text.length, button.layout.getLineEnd(button.layout.lineCount - 1))
        }
        assertEquals(0, confirmations)
        keep.performClick()
        assertEquals("Keeping audio cannot authorize removal", 0, confirmations)
        activity.finish()
    }

    @Test @Config(qualifiers = "w320dp-h640dp-mdpi")
    fun bothActionsAreVisibleOnNarrowPhone() = checkLayout(320, 640, 1f)
    @Test @Config(qualifiers = "w360dp-h640dp-mdpi")
    fun bothActionsAreVisibleWithLargeText() = checkLayout(360, 640, 2f)
    @Test @Config(qualifiers = "w640dp-h360dp-land-mdpi")
    fun bothActionsAreVisibleInLandscapeWithLargeText() = checkLayout(640, 360, 2f)

    @Test fun confirmationRequiresExplicitTapAndCannotFireTwice() {
        val activity = Robolectric.buildActivity(Activity::class.java).setup().get()
        var confirmations = 0
        val dialog = LocalAudioRemovalDialog.create(activity, 1) { confirmations++ }
        dialog.show(); ShadowLooper.idleMainLooper()
        assertEquals(0, confirmations)
        val remove = dialog.window!!.decorView.findViewWithTag<Button>("local_audio_remove")
        remove.performClick(); remove.performClick()
        assertEquals(1, confirmations)
        activity.finish()
    }
}
