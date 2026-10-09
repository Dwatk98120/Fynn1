# First Sound Helper Phoneme Analysis Server

FastAPI service for First Sound Helper.

## Local run

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8787

## Render

This server is configured for Render using the repository `render.yaml` and `server/Dockerfile`.

Render supplies the runtime `PORT` environment variable. The Dockerfile uses that port automatically.

Health endpoint:

    GET /health

API endpoint:

    POST /v1/analyze-audio

FastAPI docs:

    /docs

## Model

The default model is:

    speech31/wav2vec2-large-english-phoneme-v2

The model is large and requires enough memory for loading and inference.

## Limitations

This is a general English phoneme-recognition model, not a model validated specifically for autistic children's speech. Results are probabilistic and should not be presented as diagnosis or definitive phonological assessment.

For clinical use, the system requires appropriate evaluation on consented pediatric speech data and measurement of performance for the exact speech patterns of interest.
