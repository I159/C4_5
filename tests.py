import copy
import cProfile
import mock
import random
import string
import unittest

import C4_5.tree as tree


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.keys = [string.ascii_lowercase[i] for i in xrange(2**4)]
        self.target = 'result'
        self.learning_data = list(self.gen_data(1000))

    def gen_data(self, num_items, incons=False):
        while num_items:
            dpns = iter(((0, 1), (0, 340), (120, 560), (1000, 10000)) * 4)
            item = {k: random.randint(*next(dpns)) for k in self.keys}
            item[self.target] = sum(item.values()) / 2**4
            if incons:
                del item['b']
                incons = False
            num_items -= 1
            yield item


class PreBuildTree(BaseTestCase):
    def setUp(self):
        super(PreBuildTree, self).setUp()
        self.tree = tree.create_tree(self.learning_data, self.target)


class TestBuildTree(PreBuildTree):
    def setUp(self):
        super(TestBuildTree, self).setUp()
        self.inconsistance_data = list(self.gen_data(1000, True))

    def test_tree_health(self):
        self.assertIsNotNone(self.tree.root_node['left'])
        self.assertIsNotNone(self.tree.root_node['right'])

    def test_inconsistence_data_init(self):
        self.assertRaises(ValueError,
                tree.create_tree, self.inconsistance_data, self.target)


class TestDecide(PreBuildTree):
    def setUp(self):
        super(TestDecide, self).setUp()
        self.test_data = list(self.gen_data(100))

    def test_correct_desision(self):
        predictions = map(self.tree.make_decision, self.test_data)
        results = [i[self.target] for i in self.test_data]
        # Random generated data doesn't guarantee a good prediction. Use assert
        # for a real data.
        print len([i for i in zip(predictions, results) if i[1]>=i[0][0] and i[1]<=i[0][1]])

    def test_inconsistence_data_prediction(self):
        # TODO: determine an error case.
        inconst_test = self.gen_data(100, True)
        predictions = map(self.tree.make_decision, inconst_test)
        results = [i[self.target] for i in self.test_data]


class TestDataPreparation(BaseTestCase):
    def setUp(self):
        super(TestDataPreparation, self).setUp()
        self.ct = tree.create_tree.__decorated__(
                self.learning_data, self.target)
        self.not_numeric_data = copy.deepcopy(self.learning_data)
        self.not_numeric_data[1]['a'] = 'fvcl<'

    def test_verify_data(self):
        try:
            self.ct._verify_data(self.learning_data)
        except Exception as e:
            self.fail(e)

    def test_fail_data_verification(self):
        self.assertRaises(
                ValueError,
                self.ct._verify_data,
                self.not_numeric_data)

    def test_verify_keys(self):
        keys = set(self.learning_data[0].keys()) - set([self.target])
        self.assertEqual(self.ct._get_verified_keys(self.learning_data),
                list(keys))

    def test_keys_verification_failed(self):
        del self.learning_data[1]['a']
        self.assertRaises(
                ValueError,
                self.ct._get_verified_keys,
                self.learning_data)


class TestCreationMethods(unittest.TestCase):
    def setUp(self):
        self.learning_data = [{'a': 1, 'b': 0, 'result':0}] * 3 \
                + [{'a': 0, 'b': 1, 'result': 1}]
        self.learning_data.insert(2, {'a': 1, 'b': 1, 'result': 1})
        self.to = len(self.learning_data)
        self.ct = tree.create_tree.__decorated__(
                self.learning_data, 'result')

    def test_probability(self):
        self.assertEqual(tuple(self.ct._get_probability('a')), (.2, .8))

    def test_entropy(self):
        self.assertAlmostEqual(self.ct._count_entropy('a', 0, self.to), .72, 2)

    def test_average_entropy(self):
        entp = map(self.ct._average_entropy('a', 0, self.to),
                xrange(1, self.to-1))
        self.assertEqual(
                [(0.8112781244591328, 1), (0.9182958340544896, 2), (1.0, 3)],
                entp)

    def test_index(self):
        self.assertEqual(self.ct._min_index(0, self.to)('b')[1], 3)

    def test_key(self):
        self.assertEqual(self.ct._min_key(0, self.to)[2], 'b')

    def test_feature(self):
        self.assertEqual(
                self.ct._get_feature_values('b', 0, self.to, 3),
                (0, 1))


class TestDecisionMethod(PreBuildTree):
    def test_make_decision(self):
        unclassified = tuple(self.gen_data(100))
        res = map(self.tree.make_decision, unclassified)
        is_correct = [i for i, v in enumerate(unclassified)
                if v['result'] >= res[i][0] and v['result'] <= res[i][1]]
        print len(is_correct)
        # Since there is no real data we
        # can't check result for correctness. All possible is to ensure
        # that we have different decisions.


class TestProfile(BaseTestCase):
    def test_pof_init(self):
        cProfile.runctx(
                "tree.create_tree(self.learning_data, self.target)",
                globals(), locals())
