"""Binary ID3 decision tree.

All the features including a target feature is binary."""

import collections
import itertools
import math


class Tree(object):
    """Decision tree controller object.

    Control nodes. Maintain learning process and making decisions process."""

    parts = collections.namedtuple('DataParts', ('left', 'right'))

    def __init__(self, learning_data, target):
        """Sort a training data relatively to a target feature.

        Sort a training data relatively to a target feature to determine
        the most bound features: the smaller entropy at the data sorted
        relative to the target feature, the more bound the feature to the
        target."""

        self.target = target
        self.keys = self.get_verified_keys(learning_data)
        self.learning_data = self.get_verified_data(learning_data)
        self.root_node = None
        self.leafs = []
        self.learn()
        self.cleanup()

    def divide_sequence(self, from_, to, delimeter, key):
        left = collections.Counter(
                i[key] for i in self.learning_data[from_: delimeter])
        right = collections.Counter(
                i[key] for i in self.learning_data[delimeter: to])

        return self.parts(
                max(left, key=lambda k: left[k]),
                max(right, key=lambda k: right[k])
                )

    def get_verified_data(self, data):
        if len(set(itertools.chain(*(i.itervalues() for i in data)))) != 2:
            raise ValueError(
                    'Inconsistent data: data is not binary.')
        return sorted(data, key=lambda x: x[self.target])

    def get_verified_keys(self, learning_data):
        """Check for data consistency and return keys."""
        keys = set(tuple(i.keys()) for i in learning_data)
        if len(keys) == 1:
            return list(keys.pop())
        raise ValueError('Inconsistent data: the items have different keys.')

    def get_probability(self, key, from_=None, to=None):
        """Get probability for a different values of a key on a slice."""
        if from_ or to:
            the_slice = self.learning_data[from_:to]
        else:
            the_slice = self.learning_data
        for i in (0, 1):
            by_key = filter(lambda x: x[key] == i, the_slice)
            yield len(by_key) / float(len(the_slice))

    def count_entropy(self, key, from_, to):
        """Count entropy for a key on a slice."""
        probs = list(self.get_probability(key, from_, to))
        try:
            return sum(map(lambda p: -(p * math.log(p, 2)), probs))
        except ValueError:
            return None

    @staticmethod
    def min_entp_key(x):
        return x[0]

    def average_entropy(self, key, from_, to):
        def count(delimeter):
            entropy = filter(None,
                    (self.count_entropy(key, from_, delimeter),
                     self.count_entropy(key, delimeter, to))
                    )
            if len(entropy) == 1:
                return entropy[0], delimeter
            elif not entropy:
                return 0, delimeter
            else:
                return sum(entropy) / 2.0, delimeter
        return count

    def min_entpy_idx(self, from_, to):
        """Conunt average entropy for all allowed slices
        Return a minimum average entropy index and a prevailing
        values of the right and left side by the target key."""

        def count(key):
            ave_entropy = map(
                    self.average_entropy(key, from_, to),
                    xrange(from_+1, to-1))
            entp_dlm = min(ave_entropy, key=self.min_entp_key)
            return entp_dlm + (key, )
        return count

    def min_key_index(self, from_, to):
        keys_by_entp = map(self.min_entpy_idx(from_, to), self.keys)
        return min(keys_by_entp, key=self.min_entp_key)

    def min_entropy_leaf(self, leaf):
        from_, to = leaf['diapason']
        return self.min_key_index(from_, to) + (leaf, )

    def learn(self):
        leafs = []
        from_ = 0
        to = len(self.learning_data)
        data_target_value = collections.Counter(
                i[self.target] for i in self.learning_data)
        self.root_node = {
                'diapason': (from_, to),
                'target': max(data_target_value,
                    key=lambda k: data_target_value[k])
                }
        leafs.append(self.root_node)

        while self.keys:
            index, key, leaf = max(
                    map(self.min_entropy_leaf, leafs),
                    key=self.min_entp_key)[1:]
            leaf['key'] = key
            leaf['left'] = {'diapason': (leaf['diapason'][0], index)}
            leaf['right'] = {'diapason': (index, leaf['diapason'][1])}

            for branch in ('left', 'right'):
                if leaf[branch]['diapason'][1] - leaf[branch]['diapason'][0] > 3:
                    leafs.append(leaf[branch])

            leafs.remove(leaf)
            self.keys.remove(key)

    def make_decision(self, unclassified, node=None):
        node = node or self.root_node
        try:
            if unclassified[node['key']] == node['left']:
                return self.make_decision(unclassified, node['left_child'])
            elif unclassified[node['key']] == node['right']:
                return self.make_decision(unclassified, node['right'])
            raise ValueError('Invalid predicate value.')
        except KeyError:
            return node[self.target]

    def cleanup(self):
        delattr(self, 'keys')
        delattr(self, 'learning_data')
