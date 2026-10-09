import json
import io, os, re, uuid, json
from datetime import datetime, timezone
from typing import Optional
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoProcessor, AutoModelForCTC
from g2p_en import G2p
from analysis_engine import acoustic_features, temporal_features, evidence_scores, combined_confidence
from learning_engine import build_learning_layers, immutable_observation
from learning_store import LearningStore

MODEL_ID=os.getenv("PHONEME_MODEL","speech31/wav2vec2-large-english-phoneme-v2")
DEVICE="cuda" if torch.cuda.is_available() else "cpu"
learning_store=LearningStore()

app=FastAPI(title="First Sound Helper Phoneme API",version="0.5-13-layer")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

processor=None; model=None; g2p=None

def load_models():
    global processor,model,g2p
    if processor is None:
        processor=AutoProcessor.from_pretrained(MODEL_ID)
        model=AutoModelForCTC.from_pretrained(MODEL_ID).to(DEVICE).eval()
        g2p=G2p()

def decode_ctc(logits):
    ids=torch.argmax(logits,dim=-1).detach().cpu().tolist()[0]
    vocab=model.config.id2label
    out=[]; prev=None
    for i in ids:
        if i==prev: continue
        prev=i
        sym=vocab.get(i,"")
        if sym in ("[PAD]","[UNK]"): continue
        out.append(sym)
    return "".join(out).replace("|"," ").strip()

ARPABET_TO_IPA={
"AA":"ɑ","AE":"æ","AH":"ʌ","AO":"ɔ","AW":"aʊ","AY":"aɪ","B":"b","CH":"tʃ","D":"d","DH":"ð",
"EH":"ɛ","ER":"ɝ","EY":"eɪ","F":"f","G":"g","HH":"h","IH":"ɪ","IY":"i","JH":"dʒ","K":"k",
"L":"l","M":"m","N":"n","NG":"ŋ","OW":"oʊ","OY":"ɔɪ","P":"p","R":"ɹ","S":"s","SH":"ʃ",
"T":"t","TH":"θ","UH":"ʊ","UW":"u","V":"v","W":"w","Y":"j","Z":"z","ZH":"ʒ"
}
def g2p_ipa(word):
    phones=g2p(word)
    out=[]
    for p in phones:
        p=re.sub(r"\d","",p)
        if p in ARPABET_TO_IPA: out.append(ARPABET_TO_IPA[p])
    return "".join(out)

def tokenize_ipa(ipa):
    s=normalize_ipa(ipa); tokens=[]; i=0
    multi=("tʃ","dʒ","aɪ","aʊ","eɪ","oʊ","ɔɪ")
    while i < len(s):
        matched=next((m for m in multi if s.startswith(m,i)),None)
        if matched: tokens.append(matched); i += len(matched)
        else: tokens.append(s[i]); i += 1
    return tokens
def first_phoneme(ipa):
    t=tokenize_ipa(ipa); return t[0] if t else ""
def final_phoneme(ipa):
    t=tokenize_ipa(ipa); return t[-1] if t else ""
def normalize_ipa(s):
    return "".join(ch for ch in s if ch not in "ˈˌ ")
def phoneme_prefix_missing(expected, observed):
    e=tokenize_ipa(expected); o=tokenize_ipa(observed)
    return len(e)>1 and len(o)==len(e)-1 and e[1:]==o
def phoneme_final_missing(expected, observed):
    e=tokenize_ipa(expected); o=tokenize_ipa(observed)
    return len(e)>1 and len(o)==len(e)-1 and e[:-1]==o

def candidate_words():
    return "cat bat hat mat pat rat sat fat dog fog hog log bog pig fig big dig wig sun fun run bun gun nun top hop mop pop cop stop pot hot cot dot lot not red bed fed led wed fish dish wish feet beet meet heat meat seat tree free three bee see tea pea car far bar jar star air hair fair chair bear ear go no so show row low toe hoe snow know blue glue clue shoe one phone cone tone stone own down gown town ring sing king wing ball call fall hall mall wall all book cook look took hook mouse house out mouth south about mom dad food bird".split()

@app.get("/health")
def health():
    return {"ok":True,"model":MODEL_ID,"device":DEVICE,"apiVersion":"0.5-13-layer",
            "features":["13-layer-analytics","human-feedback-learning","speaker-adaptation","pattern-learning","strategy-learning","self-evaluation","immutable-observations"]}

@app.post("/v1/analyze-audio")
async def analyze_audio(audio:UploadFile=File(...),context:Optional[str]=Form(""),speaker_profile:Optional[str]=Form(""),human_feedback:Optional[str]=Form(""),session_id:Optional[str]=Form(""),recording_id:Optional[str]=Form(""),speaker_id:Optional[str]=Form("")):
    try:
        load_models()
        raw=await audio.read()
        samples,sr=sf.read(io.BytesIO(raw),dtype="float32")
        if samples.ndim>1: samples=samples.mean(axis=1)
        if sr!=16000: raise HTTPException(400,"Audio must be 16 kHz WAV.")
        if len(samples)<1600: raise HTTPException(400,"Please record a slightly longer sample.")

        speaker_id = (speaker_id or "").strip() or "anonymous"
        # Persistent approved learning is the default profile. A supplied profile
        # is merged only as supplemental test data and never rewrites stored history.
        profile=learning_store.get_profile(speaker_id)
        try:
            supplied_profile=json.loads(speaker_profile) if speaker_profile else {}
            if isinstance(supplied_profile,dict):
                for k,v in supplied_profile.items():
                    if k not in ("wordHistory","patternHistory","heardToMeaning","learningHistory"):
                        profile[k]=v
        except Exception:
            pass
        try: feedback=json.loads(human_feedback) if human_feedback else {}
        except Exception: feedback={}

        acoustic=acoustic_features(samples,sr)
        temporal=temporal_features(samples,sr)

        with torch.inference_mode():
            inputs=processor(samples,sampling_rate=16000,return_tensors="pt")
            logits=model(inputs.input_values.to(DEVICE)).logits
        observed=decode_ctc(logits)
        observed_ipa=normalize_ipa(observed)

        candidates=[]
        ctx=(context or "").lower()
        context_words=[]
        if "i see a" in ctx: context_words=["cat","dog","ball","car","fish","bird","house"]
        elif "i want" in ctx: context_words=["go","food","ball","car"]
        elif "look at the" in ctx: context_words=["cat","dog","ball","car","house"]
        elif "where is the" in ctx: context_words=["cat","dog","ball","car","house"]

        for w in candidate_words():
            expected=g2p_ipa(w)
            initial_missing=phoneme_prefix_missing(expected,observed_ipa)
            final_missing=phoneme_final_missing(expected,observed_ipa)
            if initial_missing or final_missing:
                c={
                    "word":w,"expectedPhonemes":expected,"observedPhonemes":observed_ipa,
                    "missingInitial":first_phoneme(expected) if initial_missing else "",
                    "missingFinal":final_phoneme(expected) if final_missing else "",
                    "possibleInitialOmission":initial_missing,
                    "possibleFinalOmission":final_missing,
                    "pattern":"initial-consonant deletion" if initial_missing else "final-consonant deletion",
                    "reason":"observed phonemes match the candidate after its initial consonant" if initial_missing else "observed phonemes match the candidate before its final consonant"
                }
                boost=0.08 if w in context_words else 0.0
                ev=evidence_scores(acoustic,temporal,observed_ipa,c)
                c["evidence"]=ev
                c["confidence"]=combined_confidence(ev,boost)
                c["learningAdaptation"]=build_learning_layers(profile=profile,candidate=c)["10_speakerAdaptation"]
                learned_map=profile.get("heardToMeaning",{}) if isinstance(profile,dict) else {}
                learned_for_heard=learned_map.get(observed.lower(),{}) if isinstance(learned_map,dict) else {}
                learned_count=int(learned_for_heard.get(w,0)) if isinstance(learned_for_heard,dict) else 0
                c["personalizedMappingCount"]=learned_count
                mapping_boost=min(0.12, 0.03 * learned_count)
                c["confidence"]=round(min(.99,c["confidence"]+c["learningAdaptation"].get("adaptationBoost",0)+mapping_boost),3)
                c["score"]=round(min(0.99,c["confidence"]),2)
                if w in context_words:
                    c["contextMatch"]=True
                candidates.append(c)

        candidates=sorted(candidates,key=lambda x:(x.get("confidence",0),x.get("score",0)),reverse=True)[:8]
        best=candidates[0] if candidates else None
        overall=best.get("confidence",0.0) if best else 0.0
        uncertainty="low" if overall>=0.85 else ("moderate" if overall>=0.60 else "high")

        # Android normally supplies these before upload. Fallback UUIDs keep
        # non-Android/API clients compatible while preserving traceability.
        session_id = (session_id or "").strip() or str(uuid.uuid4())
        recording_id = (recording_id or "").strip() or str(uuid.uuid4())
        observation_id=str(uuid.uuid4())
        created_at=datetime.now(timezone.utc).isoformat()
        raw_evidence={"acoustic":acoustic,"temporal":temporal}
        observation=immutable_observation({
            "observationId":observation_id,
            "sessionId":session_id,
            "recordingId":recording_id,
            "createdAt":created_at,
            "transcript":observed,
            "observedPhonemes":observed_ipa,
            "rawEvidence":raw_evidence,
            "audioFeatures":acoustic
        })
        # Store evidence and AI interpretation separately. Approved human feedback
        # can update the speaker profile later, but never mutates this observation.
        learning_store.save_observation(observation, speaker_id=speaker_id)
        learning_store.save_interpretation(
            observation_id=observation_id,
            recording_id=recording_id,
            speaker_id=speaker_id,
            candidates=candidates,
            best_candidate=best,
            confidence=overall,
            uncertainty=uncertainty,
            context=context or "",
        )
        learning_history=profile.get("learningHistory",{}) if isinstance(profile,dict) else {}
        learning=build_learning_layers(profile=profile,feedback=feedback,history=learning_history,candidate=best or {})
        return {
            "model":MODEL_ID,
            "speakerId":speaker_id,
            "sessionId":session_id,
            "recordingId":recording_id,
            "observation":observation,
            "transcript":observed,
            "analysis":{
                "status":"probabilistic",
                "observationPolicy":"IMMUTABLE: learning layers may annotate, but may not rewrite transcript, observed phonemes, raw evidence, or audio features.",
                "possibleInitialConsonantOmission":any(c["possibleInitialOmission"] for c in candidates),
                "possibleFinalConsonantOmission":any(c["possibleFinalOmission"] for c in candidates),
                "overallConfidence":overall,
                "uncertaintyBand":uncertainty,
                "evidence":{
                    "acoustic":acoustic,
                    "temporal":temporal
                },
                "learningLayers":learning,
                "note":"AI-assisted candidate analysis. Evidence and confidence are for communication support/testing, not a clinical determination."
            },
            "candidates":candidates
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500,detail=f"analysis_failed: {type(e).__name__}")


@app.post("/v1/learning/feedback")
async def submit_learning_feedback(
    observation_id: str = Form(...),
    speaker_id: str = Form(...),
    recording_id: Optional[str] = Form(""),
    confirmed_word: Optional[str] = Form(""),
    corrected_word: Optional[str] = Form(""),
    approved_for_learning: bool = Form(False),
):
    """Record caregiver feedback. Only explicitly approved examples update learning."""
    try:
        return learning_store.submit_feedback(
            speaker_id=speaker_id,
            observation_id=observation_id,
            recording_id=recording_id or "",
            confirmed_word=confirmed_word or "",
            corrected_word=corrected_word or "",
            approved_for_learning=bool(approved_for_learning),
            source="caregiver",
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@app.get("/v1/learning/profile/{speaker_id}")
def learning_profile(speaker_id: str):
    """Return the current approved-learning profile for one anonymous speaker ID."""
    p=learning_store.get_profile(speaker_id)
    h=p.get("learningHistory",{}) if isinstance(p,dict) else {}
    evaluated=int(h.get("evaluated",0))
    correct=int(h.get("correct",0))
    return {
        "speakerId":p.get("speakerId",speaker_id),
        "approvedExamples":int(p.get("approvedExamples",0)),
        "learnedWords":p.get("wordHistory",{}),
        "learnedPatterns":p.get("patternHistory",{}),
        "evaluated":evaluated,
        "correct":correct,
        "estimatedTopCandidateAccuracy":round(correct/evaluated,3) if evaluated else None,
    }


@app.get("/v1/learning/integrity")
def learning_integrity():
    """Verify hashes of all stored immutable observations."""
    return learning_store.integrity_status()
