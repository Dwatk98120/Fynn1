# Trial AI Architecture

## Android
Android records/loads 16 kHz mono WAV and calls:
`POST /v1/analyze-audio`

The Android client remains compatible with the existing API contract and now displays
the enhanced overall candidate confidence when supplied.

## legacy cloud backend/FastAPI
The server runs:
1. Wav2Vec2 phoneme inference
2. CTC decoding
3. Candidate-word matching
4. Acoustic evidence extraction
5. Temporal evidence extraction
6. Candidate evidence fusion
7. Conservative confidence/uncertainty band
8. Structured JSON result

## Parent PC
The Parent PC is a review and batch-analysis client. It does not duplicate the speech model.
It reads the same API results and keeps analysis history locally.

## Important limitation
This trial does not claim clinical accuracy or fully autonomous intent inference.
The confidence/evidence layer is an engineering experiment around the current phoneme model.
Personalized learning and longitudinal analytics remain local/review-oriented until their
data model and validation are explicitly implemented.
