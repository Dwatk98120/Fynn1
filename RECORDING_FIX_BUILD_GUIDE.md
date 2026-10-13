# Recording indicator build verification

The status row always displays `Not Recording - INDICATOR V2` between Record speech and Stop. During recording it pulses red with `RECORDING - INDICATOR V2`.

IMPORTANT: GitHub Actions builds from the repository ROOT. Upload the CONTENTS of `Hearlium_Complete_Rebuild/` into the repository root, not the enclosing folder. The `.github/workflows/build-apk.yml` must also be updated in the root.

On Actions use the workflow from the branch containing these files. Verify the source-check and compiled-resource-check steps succeed. Uninstall the old APK, then install the new artifact.

Not yet compiled or device-tested here. The resource check detects the ID, not runtime rendering.
