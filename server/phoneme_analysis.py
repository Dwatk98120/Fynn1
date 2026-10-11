from __future__ import annotations

from typing import Iterable

VOWELS = {"i","ɪ","e","ɛ","æ","ɑ","ɒ","ɔ","ʌ","ə","ɚ","ɝ","ʊ","u","aɪ","aʊ","eɪ","oʊ","ɔɪ"}
CONSONANTS = {"p","b","t","d","k","g","f","v","θ","ð","s","z","ʃ","ʒ","h","tʃ","dʒ","m","n","ŋ","l","ɹ","j","w"}

FEATURES = {
    "p":{"type":"consonant","manner":"stop","place":"bilabial","voicing":"voiceless"},
    "b":{"type":"consonant","manner":"stop","place":"bilabial","voicing":"voiced"},
    "t":{"type":"consonant","manner":"stop","place":"alveolar","voicing":"voiceless"},
    "d":{"type":"consonant","manner":"stop","place":"alveolar","voicing":"voiced"},
    "k":{"type":"consonant","manner":"stop","place":"velar","voicing":"voiceless"},
    "g":{"type":"consonant","manner":"stop","place":"velar","voicing":"voiced"},
    "f":{"type":"consonant","manner":"fricative","place":"labiodental","voicing":"voiceless"},
    "v":{"type":"consonant","manner":"fricative","place":"labiodental","voicing":"voiced"},
    "θ":{"type":"consonant","manner":"fricative","place":"dental","voicing":"voiceless"},
    "ð":{"type":"consonant","manner":"fricative","place":"dental","voicing":"voiced"},
    "s":{"type":"consonant","manner":"fricative","place":"alveolar","voicing":"voiceless"},
    "z":{"type":"consonant","manner":"fricative","place":"alveolar","voicing":"voiced"},
    "ʃ":{"type":"consonant","manner":"fricative","place":"postalveolar","voicing":"voiceless"},
    "ʒ":{"type":"consonant","manner":"fricative","place":"postalveolar","voicing":"voiced"},
    "h":{"type":"consonant","manner":"fricative","place":"glottal","voicing":"voiceless"},
    "tʃ":{"type":"consonant","manner":"affricate","place":"postalveolar","voicing":"voiceless"},
    "dʒ":{"type":"consonant","manner":"affricate","place":"postalveolar","voicing":"voiced"},
    "m":{"type":"consonant","manner":"nasal","place":"bilabial","voicing":"voiced"},
    "n":{"type":"consonant","manner":"nasal","place":"alveolar","voicing":"voiced"},
    "ŋ":{"type":"consonant","manner":"nasal","place":"velar","voicing":"voiced"},
    "l":{"type":"consonant","manner":"approximant","place":"alveolar","voicing":"voiced"},
    "ɹ":{"type":"consonant","manner":"approximant","place":"postalveolar","voicing":"voiced"},
    "j":{"type":"consonant","manner":"approximant","place":"palatal","voicing":"voiced"},
    "w":{"type":"consonant","manner":"approximant","place":"labial-velar","voicing":"voiced"},
    "i":{"type":"vowel","height":"close","backness":"front"},
    "ɪ":{"type":"vowel","height":"near-close","backness":"front"},
    "e":{"type":"vowel","height":"close-mid","backness":"front"},
    "ɛ":{"type":"vowel","height":"open-mid","backness":"front"},
    "æ":{"type":"vowel","height":"near-open","backness":"front"},
    "ɑ":{"type":"vowel","height":"open","backness":"back"},
    "ɔ":{"type":"vowel","height":"open-mid","backness":"back"},
    "ʌ":{"type":"vowel","height":"open-mid","backness":"central"},
    "ə":{"type":"vowel","height":"mid","backness":"central"},
    "ɚ":{"type":"vowel","height":"mid","backness":"central"},
    "ɝ":{"type":"vowel","height":"mid","backness":"central"},
    "ʊ":{"type":"vowel","height":"near-close","backness":"back"},
    "u":{"type":"vowel","height":"close","backness":"back"},
    "aɪ":{"type":"vowel","kind":"diphthong"},
    "aʊ":{"type":"vowel","kind":"diphthong"},
    "eɪ":{"type":"vowel","kind":"diphthong"},
    "oʊ":{"type":"vowel","kind":"diphthong"},
    "ɔɪ":{"type":"vowel","kind":"diphthong"},
}

def phoneme_features(symbol: str) -> dict:
    base = dict(FEATURES.get(symbol, {}))
    if not base:
        if symbol in VOWELS: base["type"] = "vowel"
        elif symbol in CONSONANTS: base["type"] = "consonant"
        else: base["type"] = "unknown"
    return base

def classify_confidence(confidence: float) -> str:
    if confidence >= 0.80: return "clear"
    if confidence >= 0.58: return "moderate"
    if confidence >= 0.38: return "uncertain"
    return "distorted_or_unclear"

def summarize_observed_phonemes(tokens: Iterable[str], confidences: Iterable[float] | None = None) -> dict:
    tokens = list(tokens or [])
    confs = list(confidences or [])
    if len(confs) < len(tokens): confs.extend([0.65] * (len(tokens) - len(confs)))
    confs = confs[:len(tokens)]
    evidence=[]; consonant_count=0; vowel_count=0; uncertain=[]
    for idx, token in enumerate(tokens):
        conf=max(0.0,min(1.0,float(confs[idx])))
        features=phoneme_features(token)
        if features.get("type")=="consonant": consonant_count += 1
        elif features.get("type")=="vowel": vowel_count += 1
        clarity=classify_confidence(conf)
        item={"phoneme":token,"index":idx,"confidence":round(conf,3),"clarity":clarity,"features":features}
        evidence.append(item)
        if clarity in ("uncertain","distorted_or_unclear"): uncertain.append(item)
    overall=sum(confs)/len(confs) if confs else 0.0
    return {"phonemeCount":len(tokens),"consonantCount":consonant_count,"vowelCount":vowel_count,
            "overallPhonemeConfidence":round(overall,3),"confidenceBand":classify_confidence(overall) if tokens else "no_phonemes",
            "phonemeEvidence":evidence,"uncertainOrDistorted":uncertain,"uncertainCount":len(uncertain)}

def substitution_similarity(expected: str, observed: str) -> dict:
    e=phoneme_features(expected); o=phoneme_features(observed); shared=[]; compared=[]
    if e.get("type")=="consonant" and o.get("type")=="consonant":
        for key in ("manner","place","voicing"):
            if key in e and key in o:
                compared.append(key)
                if e[key]==o[key]: shared.append(key)
    elif e.get("type")=="vowel" and o.get("type")=="vowel":
        for key in ("height","backness","kind"):
            if key in e and key in o:
                compared.append(key)
                if e[key]==o[key]: shared.append(key)
    similarity=(len(shared)/len(compared)) if compared else 0.0
    return {"expectedFeatures":e,"observedFeatures":o,"sharedFeatures":shared,"featureSimilarity":round(similarity,3)}
