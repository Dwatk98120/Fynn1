"""Read-only adult 18-word regression benchmark. Never modifies evidence or learning."""
import argparse, json, re
from pathlib import Path

EXPECTED = ['three','tree','free','thin','tin','fin','ship','chip','sip','cat','call','fall','dog','log','fog','cat','bat','pat']
PHONEMES = ['θri','tri','fri','θɪn','tɪn','fɪn','ʃɪp','tʃɪp','sɪp','kæt','kɔl','fɔl','dɔg','lɔg','fɔg','kæt','bæt','pæt']

def normalized_words(text):
    return ['three' if x == '3' else x for x in re.findall(r"[a-z]+|\d+", (text or '').lower())]

def normalize_ipa(s):
    return (s or '').replace('ʧ','tʃ').replace('ʤ','dʒ').replace('ɹ','r')

def evaluate(payload):
    result=payload.get('analysisResult',payload)
    word=result.get('wordRecognition',{})
    observed=normalized_words(word.get('text',''))
    raw=normalize_ipa(result.get('transcript',''))
    parts=raw.split()
    comparisons=[]
    for i,target in enumerate(EXPECTED):
        actual=observed[i] if i<len(observed) else None
        ph=parts[i] if i<len(parts) else None
        comparisons.append({'index':i+1,'expected':target,'wordHypothesis':actual,'wordCorrect':actual==target,
                            'expectedPhonemes':PHONEMES[i],'observedPhonemes':ph,
                            'phonemeExact':ph==PHONEMES[i] if ph is not None else None})
    return {'status':'offline_benchmark_only','adultTestOnly':True,'recordingId':payload.get('recordingId',result.get('recordingId')),
            'expectedWordCount':len(EXPECTED),'observedWordCount':len(observed),
            'wordExactCount':sum(x['wordCorrect'] for x in comparisons),
            'wordAccuracy':round(sum(x['wordCorrect'] for x in comparisons)/len(EXPECTED),4),
            'phonemeExactCount':sum(x['phonemeExact'] is True for x in comparisons),
            'phonemeAlignedCount':min(len(parts),len(EXPECTED)),
            'warning':'Fixed test-word alignment only; not general word alignment or clinical accuracy. Phoneme spelling varies by dialect. No learning approval.',
            'items':comparisons}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('analysis_json',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    report=evaluate(json.loads(a.analysis_json.read_text(encoding='utf-8')))
    content=json.dumps(report,indent=2,ensure_ascii=False)
    if a.output: a.output.write_text(content+'\n',encoding='utf-8')
    else: print(content)
