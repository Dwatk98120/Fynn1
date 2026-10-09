# First Sound Helper — Parent PC AI Trial

This trial PC client connects to the Render/FastAPI backend in the project and adds:
- AI dashboard
- evidence view
- confidence/uncertainty display
- batch WAV analysis
- local analysis-result history
- recurring candidate-word analytics
- raw JSON inspection
- configurable Render API URL

Run on Windows with Python 3.10+:
1. Open this folder in File Explorer.
2. Double-click `run_parent_pc.bat`.
3. Click **Test Connection**.
4. Select a 16 kHz mono WAV and click **Analyze**.

The server remains the source of speech/phoneme analysis. The PC stores results locally under:
`%USERPROFILE%\FirstSoundHelper_ParentPC\analysis_results`

This is a development/trial tool. The evidence and confidence fields are model/heuristic signals for communication-support testing, not clinical measurements.
