import unittest
from phase3_consonant_regression import evaluate, EXPECTED
class RegressionTests(unittest.TestCase):
    def test_perfect_words(self):
        data={'wordRecognition':{'text':', '.join(EXPECTED)},'transcript':' '.join(['θri']*18)}
        self.assertEqual(evaluate(data)['wordExactCount'],18)
    def test_three_is_not_tree_or_free(self):
        data={'wordRecognition':{'text':'3, 3, 3, thin, thin, thin, chip, chip, sip, cat, call, fall, dog, log, fog, cat, bat, pat'},'transcript':''}
        report=evaluate(data)
        self.assertEqual(report['wordExactCount'],13)
        self.assertEqual(report['items'][1]['wordCorrect'],False)
    def test_missing_words_never_count_as_correct(self):
        self.assertEqual(evaluate({})['wordExactCount'],0)
    def test_nested_analysis(self):
        self.assertEqual(evaluate({'analysisResult':{'wordRecognition':{'text':'three'}}})['observedWordCount'],1)
if __name__=='__main__': unittest.main()
