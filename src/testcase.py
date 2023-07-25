from src.query import Query


class TestCase:

    OR_TEST_CONDITION = 'OR'
    AND_TEST_CONDITION = 'AND'

    def __init__(self, test_query, condition_queries=None, test_condition=OR_TEST_CONDITION):
        if condition_queries is None:
            condition_queries = []
        if type(test_query) is list:
            self._test_queries = test_query
        else:
            self._test_queries = [test_query]
        self._condition_queries = condition_queries
        self._test_condition = test_condition

    def get_test_queries(self):
        return self._test_queries

    def get_test_condition(self):
        return self._test_condition

    def get_condition_queries(self):
        return self._condition_queries

    def to_dict(self):
        return {
            'test_queries': [query.to_dict() for query in self._test_queries],
            'test_condition': self._test_condition,
            'condition_queries': [query.to_dict() for query in self._condition_queries]
        }

    @staticmethod
    def from_dict(d):
        tests = [Query.from_dict(test) for test in d['test_queries']]
        test_condition = d['test_condition']
        conditions = [Query.from_dict(condition) for condition in d['condition_queries']]
        return TestCase(tests, conditions, test_condition)

    def __str__(self):
        res = 'Test Queries:\n'
        for query in self._test_queries:
            query_dict = query.to_dict()
            res += f"Query: {query_dict['prompt']}, " \
                   f"Answer: {query_dict['answers'][0]['value']}\n"
        res += f'Test Condition: {self._test_condition}\n'
        res += 'Condition Queries:\n'
        for query in self._condition_queries:
            query_dict = query.to_dict()
            res += f"Query: {query_dict['prompt']}, " \
                   f"Answer: {query_dict['answers'][0]['value']}\n"
        return res
