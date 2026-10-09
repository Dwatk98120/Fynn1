"""Learning layers 9-13 for First Sound Helper.

Design rule: observations are immutable. Learning may add annotations, feedback,
profiles and evaluation records, but never edits the original observation fields.
"""
from copy import deepcopy
from datetime import datetime, timezone

OBSERVATION_FIELDS = ("transcript", "observedPhonemes", "rawEvidence", "audioFeatures")

def utc_now(): return datetime.now(timezone.utc).isoformat()

def layer9_human_feedback(feedback=None):
    f=feedback if isinstance(feedback,dict) else {}
    return {"status":"unconfirmed" if not f else "confirmed_or_corrected",
            "confirmedWord":f.get("confirmedWord",""),
            "correctedWord":f.get("correctedWord",""),
            "confidence":f.get("confidence",None),
            "source":"human_feedback" if f else "none",
            "timestamp":utc_now()}

def layer10_speaker_adaptation(profile=None,candidate=None):
    p=profile if isinstance(profile,dict) else {}
    c=candidate if isinstance(candidate,dict) else {}
    wh=p.get("wordHistory",{}) if isinstance(p.get("wordHistory",{}),dict) else {}
    ph=p.get("patternHistory",{}) if isinstance(p.get("patternHistory",{}),dict) else {}
    w=c.get("word",""); pat=c.get("pattern","")
    return {"profileAvailable":bool(profile),"wordCount":int(wh.get(w,0)),
            "patternCount":int(ph.get(pat,0)),"adaptationBoost":min(.08,.01*min(int(wh.get(w,0)),8)+.01*min(int(ph.get(pat,0)),8))}

def layer11_pattern_learning(history=None):
    h=history if isinstance(history,dict) else {}
    return {"examples":int(h.get("examples",0)),"recurringPatterns":h.get("patterns",{}),
            "recurringWords":h.get("words",{}),"learningReady":int(h.get("examples",0))>=3}

def layer12_strategy_learning(history=None):
    h=history if isinstance(history,dict) else {}
    strategies=h.get("strategies",{}) if isinstance(h.get("strategies",{}),dict) else {}
    ranked=sorted(strategies.items(),key=lambda kv: kv[1].get("successRate",0) if isinstance(kv[1],dict) else 0,reverse=True)
    return {"testedStrategies":len(strategies),"bestNextStrategy":ranked[0][0] if ranked else "none",
            "strategyEvidence":dict(ranked[:5])}

def layer13_self_evaluation(history=None):
    h=history if isinstance(history,dict) else {}
    total=int(h.get("evaluated",0)); correct=int(h.get("correct",0))
    acc=(correct/total) if total else None
    return {"evaluated":total,"correct":correct,"accuracy":round(acc,3) if acc is not None else None,
            "calibrationReady":total>=10,"needsHumanReview":total<10}

def build_learning_layers(profile=None,feedback=None,history=None,candidate=None):
    return {"9_humanFeedback":layer9_human_feedback(feedback),
            "10_speakerAdaptation":layer10_speaker_adaptation(profile,candidate),
            "11_patternLearning":layer11_pattern_learning(history),
            "12_strategyLearning":layer12_strategy_learning(history),
            "13_selfEvaluation":layer13_self_evaluation(history)}

def immutable_observation(record):
    """Return a frozen-at-creation snapshot. Learning layers must not overwrite it."""
    src=record if isinstance(record,dict) else {}
    return {"observationId":src.get("observationId"),
            "sessionId":src.get("sessionId"),
            "recordingId":src.get("recordingId"),
            "createdAt":src.get("createdAt"),
            "transcript":src.get("transcript",""),
            "observedPhonemes":src.get("observedPhonemes",""),
            "rawEvidence":deepcopy(src.get("rawEvidence",{})),
            "audioFeatures":deepcopy(src.get("audioFeatures",{}))}
