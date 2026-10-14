Hearlium Parent PC local package - October 13, 2026

This is a repackaging of the previously available Fynn1 Parent PC source snapshot, with the uploaded server/main.py error-logging version corrected to remove a duplicate local datetime import. It is NOT a freshly downloaded GitHub branch snapshot.

To use:
1. Extract to a NEW folder, not over a running installation.
2. Run parent_pc_local/setup_and_start.bat to launch the local server.
3. Keep the server command window open and use the Android app on the same network.
4. If NLTK reports missing averaged_perceptron_tagger_eng, open PowerShell in the extracted project folder and run:
   .\.venv\Scripts\python.exe -m nltk.downloader averaged_perceptron_tagger_eng
   (If Python environment is stored elsewhere, use its python.exe instead.)

This is source/build content, not a compiled Windows installer. Back up your existing learning data before replacing installations.
