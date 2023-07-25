import random
from enum import Enum, auto
import json
from pathlib import Path

from fact import Fact
from testcase import TestCase


class TestsAxis(Enum):
    MAKING_UP = auto()
    LOGICAL_CONSTRAINTS = auto()
    SUBJECT_PARAPHRASING = auto()
    TWO_HOP = auto()
    FORWARD_TWO_HOP = auto()
    PREVIOUS_STORAGE = auto()


class Example:

    def __init__(self,
                 fact: Fact,
                 making_up_tests: list = [],
                 logical_constraints: list = [],
                 subject_paraphrasing_tests: list = [],
                 two_hop_tests: list = [],
                 forward_two_hop_tests: list = [],
                 prev_storage_tests: list = []):
        self.fact = fact
        self.making_up_tests = making_up_tests
        self.logical_constraints = logical_constraints
        self.subject_paraphrasing_tests = subject_paraphrasing_tests
        self.two_hop_tests = two_hop_tests
        self.forward_two_hop_tests = forward_two_hop_tests
        self.prev_storage_tests = prev_storage_tests

    def create_example_dict(self, example_type):
        return {
            'example_type': example_type,
            'edit': self.fact.to_dict(),
            'Relation_Specificity': [test.to_dict() for test in self.making_up_tests],
            'Logical_Generalization': [test.to_dict() for test in self.logical_constraints],
            'Subject_Aliasing': [test.to_dict() for test in self.subject_paraphrasing_tests],
            'Compositionality_I': [test.to_dict() for test in self.two_hop_tests],
            'Compositionality_II': [test.to_dict() for test in self.forward_two_hop_tests],
            'Forgetfulness': [test.to_dict() for test in self.prev_storage_tests],
        }

    @staticmethod
    def from_dict(d):
        fact = Fact.from_dict(d['edit'])
        making_up_tests = [TestCase.from_dict(test) for test in d['Relation_Specificity']]
        logical_constraints = [TestCase.from_dict(test) for test in d['Logical_Generalization']]
        subject_paraphrasing_tests = [TestCase.from_dict(test) for test in d['Subject_Aliasing']]
        two_hop_tests = [TestCase.from_dict(test) for test in d['Compositionality_I']]
        forward_two_hop_tests = [TestCase.from_dict(test) for test in d['Compositionality_II']]
        prev_storage_tests = [TestCase.from_dict(test) for test in d['Forgetfulness']]
        if d['example_type'] in ['random', 'popular']:
            previous_fact = Fact.from_dict(d['edit']['previous_fact'])
            return CounterFactualExample(fact, previous_fact, making_up_tests, logical_constraints,
                                         subject_paraphrasing_tests, two_hop_tests, forward_two_hop_tests, prev_storage_tests)
        elif d['example_type'] == 'recent':
            return RecentlyAddedExample(fact, making_up_tests, logical_constraints, subject_paraphrasing_tests,
                                        two_hop_tests, forward_two_hop_tests, prev_storage_tests)
        else:
            print('Unknown fact type')

    def __str__(self):
        res = f'Fact: {str(self.fact)}\n'
        res += f'Making Up tests:\n'
        res += self.str_list_of_tests(self.making_up_tests)
        res += '\n'
        res += f'Logical Constraints:\n'
        res += self.str_list_of_tests(self.logical_constraints)
        res += '\n'
        res += f'Subject Paraphrasing tests:\n'
        res += self.str_list_of_tests(self.subject_paraphrasing_tests)
        res += '\n'
        res += f'Two-Hop tests:\n'
        res += self.str_list_of_tests(self.two_hop_tests)
        res += '\n'
        res += f'Forward Two-Hop tests:\n'
        res += self.str_list_of_tests(self.forward_two_hop_tests)
        res += '\n'
        res += f'Previous Storage tests:'
        res += self.str_list_of_tests(self.prev_storage_tests)
        res += '\n'
        return res
    
    @staticmethod
    def str_list_of_tests(tests: list):
        res = ''
        for test in tests:
            res += f'{str(test)}\n'
        return res


class CounterFactualExample(Example):

    def __init__(self,
                 fact: Fact,
                 previous_fact: Fact,
                 making_up_tests: list = [],
                 logical_constraints: list = [],
                 subject_paraphrasing_tests: list = [],
                 two_hop_tests: list = [],
                 forward_two_hop_tests: list = [],
                 prev_storage_tests: list = []
                 ):
        super().__init__(
            fact,
            making_up_tests,
            logical_constraints,
            subject_paraphrasing_tests,
            two_hop_tests,
            forward_two_hop_tests,
            prev_storage_tests
        )
        self.previous_fact = previous_fact

    def to_dict(self):
        d = super().create_example_dict('counter_fact')
        d['edit']['previous_fact'] = self.previous_fact.to_dict()
        return d

    def __str__(self):
        res = super().__str__()
        res += f'Previous Fact: {str(self.previous_fact)}\n'
        return res


class RecentlyAddedExample(Example):

    def __init__(self,
                 fact: Fact,
                 making_up_tests: list = [],
                 logical_constraints: list = [],
                 subject_paraphrasing_tests: list = [],
                 two_hop_tests: list = [],
                 forward_two_hop_tests: list = [],
                 prev_storage_tests: list = []
                 ):
        super().__init__(
            fact,
            making_up_tests,
            logical_constraints,
            subject_paraphrasing_tests,
            two_hop_tests,
            forward_two_hop_tests,
            prev_storage_tests
        )

    def to_dict(self):
        return super().create_example_dict('recently_added_fact')


class Dataset:

    def __init__(self, examples: list):
        self.examples = examples

    def sample(self, k: int):
        return random.sample(self.examples, min(k, len(self.examples)))

    def to_file(self, filename):
        p = Path(filename)
        p.parent.mkdir(parents=True, exist_ok=True)
        d = [example.to_dict() for example in self.examples]
        with p.open('w+', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

    @staticmethod
    def from_file(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            examples = json.load(f)
        return Dataset([Example.from_dict(example) for example in examples])
