Hearlium Branch 2: Word Merge + Segment Confidence Repair

Based on Segmentation Safety Repair source. Includes full source tree.
Changes are Parent PC server only; Android remains unchanged.

1. Suggest merges for adjacent short phoneme fragments separated by <= 0.25 seconds only if the best candidate improves by > 0.02. Original wordSegments remain unchanged.
2. Add mergedSegmentCandidates and segmentInterpretation to API JSON.
3. Add segmentCandidateConfidence and segmentCandidateCoverage under analysis, without misrepresenting legacy overallConfidence as word accuracy.
4. Aggregate possible initial/final omission flags across selected segment interpretations.
5. Include unit tests for merges, pauses, and omission reporting.

Deploy: replace your Branch 2 source with this complete source tree, commit/push to GitHub, rebuild Parent PC installer with existing BUILD_HEARLIUM_INSTALLER.bat, install and record counting 1-12 again. Keep a backup of current working source first.

Important: merged candidates are unconfirmed interpretations, not verified words. No automatic speaker learning is enabled by this patch.
