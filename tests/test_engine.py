import unittest
from review_engine.core import normalize, extract, aggregate, build_index, retrieve
from agent import load_evidence, analyze, parse_request

CFG = {
    'aspects': {'sound': ['sound'], 'battery': ['battery']},
    'scenes': {'gym': ['gym']},
    'positive': ['good', 'great'],
    'negative': ['bad', 'poor'],
    'negations': ['not'],
    'quality_cues': ['stopped working'],
}


class EngineTests(unittest.TestCase):
    def test_aspect_separation_and_negation(self):
        r = normalize({'product_id': 'x', 'text': 'The sound is great but the battery is not good.'}, 1)
        rows = extract(r, CFG)
        self.assertEqual({x['aspect']: x['sentiment'] for x in rows}, {'sound': 'positive', 'battery': 'negative'})
        for row in rows:
            self.assertEqual(r['text'][row['start']:row['end']], row['evidence'])
        self.assertFalse(any(row['evidence'].startswith('ut ') for row in rows))

    def test_no_rating_fallback(self):
        r = normalize({'product_id': 'x', 'text': 'The battery lasts 4 hours.', 'rating': 5}, 1)
        self.assertEqual(extract(r, CFG)[0]['sentiment'], 'unknown')

    def test_review_dedup_and_mixed(self):
        common = {'product_id': 'p', 'aspect': 'sound', 'scene': 'gym'}
        rows = [
            dict(common, review_id='1', sentiment='positive'),
            dict(common, review_id='1', sentiment='negative'),
            dict(common, review_id='2', sentiment='positive'),
        ]
        result = aggregate(rows, 2)[0]
        self.assertEqual((result['review_count'], result['mixed'], result['positive']), (2, 1, 1))
        self.assertFalse(result['sufficient'])

    def test_retrieval_filters_and_empty(self):
        rows = [
            {'review_id': 'a', 'product_id': 'p', 'aspect': 'sound', 'scene': 'gym', 'evidence': 'great sound for running'},
            {'review_id': 'b', 'product_id': 'q', 'aspect': 'sound', 'scene': 'gym', 'evidence': 'great sound for music'},
        ]
        v, m = build_index(rows)
        self.assertEqual(retrieve(rows, v, m, 'sound', product_id='p')[0]['review_id'], 'a')
        self.assertEqual(retrieve(rows, v, m, 'unmatchedword'), [])

    def test_agent_v2_earbuds_and_smartwatch(self):
        aspects, scenes = parse_request('跑步时想要佩戴稳定且舒适的耳机', category='无线耳机')
        self.assertIn('佩戴稳定', aspects)
        self.assertIn('佩戴舒适', aspects)
        self.assertIn('运动', scenes)

        df_ear = load_evidence(category='无线耳机')
        res_ear = analyze(df_ear, '通勤地铁需要降噪和音质', minimum=20, category='无线耳机')
        self.assertIsNone(res_ear['question'])
        self.assertEqual(len(res_ear['products']), 3)
        self.assertIn('local_summary', res_ear)
        self.assertTrue(len(res_ear['local_summary']) > 50)

        df_watch = load_evidence(category='智能手表')
        res_watch = analyze(df_watch, '想找续航长、运动心率监测准的手表', minimum=10, category='智能手表')
        self.assertIsNone(res_watch['question'])
        self.assertEqual(len(res_watch['products']), 3)
        self.assertIn('续航与充电', res_watch['aspects'])


if __name__ == '__main__':
    unittest.main()
