"""Frozen build gate for 0.4.16, using generated review data only."""


def run_check():
    from server.phoneme_substitution import analyze_substitutions
    from server.review_vocabulary import NUMBER_PHRASES, COMMON_SENTENCE_WORDS
    from server.utterance_prosody_review import review_utterance_prosody
    from server.recognition_diagnostics import review_recognition
    if analyze_substitutions(['ɹ','ɛ','d'], ['r','ɛ','d'])['editCount'] != 0:
        raise RuntimeError('Frozen rhotic comparison is outdated')
    if len(NUMBER_PHRASES) != 50 or 'forty nine' not in NUMBER_PHRASES or 'cars' not in COMMON_SENTENCE_WORDS:
        raise RuntimeError('Frozen vocabulary is outdated')
    prosody = {'available': True, 'energyPeakTimesSeconds': [i + .2 for i in range(20)],
               'estimatedSyllablePeaks': 20, 'stressPattern': [{'timeSeconds': i+.2} for i in range(12)]}
    voice = {'status': 'evaluated', 'speechSegments': [{'startSeconds': 0, 'endSeconds': 20}]}
    rate = review_utterance_prosody(prosody, voice)
    if rate['utteranceIntervals'][0]['estimatedSyllablePeaks'] != 20:
        raise RuntimeError('Frozen prosody still uses a truncated preview')
    source = {'wordRecognition': {'text': 'two two', 'segments': []}}
    review = review_recognition(source)
    if review['timingTokenCountsMatch'] or source['wordRecognition']['text'] != 'two two':
        raise RuntimeError('Frozen diagnostics changed words or missed absent timing')
    return True
