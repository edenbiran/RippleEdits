import argparse

from benchmark import Dataset, RecentlyAddedExample, CounterFactualExample
from queryexecutor import GPT2QueryExecutor, GPTJQueryExecutor, GPTNeoXQueryExecutor, LlamaQueryExecutor, \
    GPT3QueryExecutor
from testrunner import TestRunner, ExampleResult, TestResult


def get_query_executor(model_name):
    if model_name.startswith('gpt2-'):
        mode_size = model_name.split('-')[1]
        return GPT2QueryExecutor(mode_size)
    elif model_name == 'gpt-j':
        return GPTJQueryExecutor()
    elif model_name == 'gpt-neox':
        return GPTNeoXQueryExecutor()
    elif model_name.startswith('llama-'):
        mode_size = model_name.split('-')[1]
        return LlamaQueryExecutor(mode_size)
    elif model_name == 'gpt-3':
        return GPT3QueryExecutor()
    else:
        raise Exception('Unknown model name')


def filter_tests(test_runner, example, testcases, include_all_facts):
    example_result, test_results = test_runner.run_testcases(example, testcases)
    if not include_all_facts and example_result != ExampleResult.EXECUTED:
        return None
    return [test for test in testcases if test not in test_results[TestResult.NOT_EXECUTED]]


def main(args):
    print('Loading dataset')
    dataset = Dataset.from_file(args.benchmark)
    print('Loading model')
    query_executor = get_query_executor(args.model)
    test_runner = TestRunner(query_executor, None)
    filtered_examples = []
    test_count = 0
    filtered_test_count = 0

    for i, example in enumerate(dataset.examples):
        print(f'Example {i + 1} / {len(dataset.examples)}: {example.fact.to_dict()}')

        test_count += len(example.making_up_tests) + len(example.logical_constraints) + \
                      len(example.subject_paraphrasing_tests) + len(example.two_hop_tests) + \
                      len(example.prev_storage_tests)
        prev_filtered_test_count = filtered_test_count

        filtered_making_up_tests = filter_tests(test_runner, example, example.making_up_tests, args.include_all_facts)
        filtered_test_count += len(filtered_making_up_tests)

        if filtered_making_up_tests is None:  # Example shouldn't be included at all
            continue

        filtered_logical_constraints = filter_tests(test_runner, example, example.logical_constraints,
                                                    args.include_all_facts)
        filtered_test_count += len(filtered_logical_constraints)

        filtered_subject_paraphrasing_tests = filter_tests(test_runner, example, example.subject_paraphrasing_tests,
                                                           args.include_all_facts)
        filtered_test_count += len(filtered_subject_paraphrasing_tests)

        filtered_two_hop_tests = filter_tests(test_runner, example, example.two_hop_tests, args.include_all_facts)
        filtered_test_count += len(filtered_two_hop_tests)

        filtered_prev_storage_tests = filter_tests(test_runner, example, example.prev_storage_tests,
                                                   args.include_all_facts)
        filtered_test_count += len(filtered_prev_storage_tests)

        if prev_filtered_test_count == filtered_test_count:  # Example has no tests that passed the filter
            continue

        if isinstance(example, RecentlyAddedExample):
            filtered_examples.append(RecentlyAddedExample(example.fact, filtered_making_up_tests,
                                                          filtered_logical_constraints,
                                                          filtered_subject_paraphrasing_tests,
                                                          filtered_two_hop_tests, filtered_prev_storage_tests))
        elif isinstance(example, CounterFactualExample):
            filtered_examples.append(CounterFactualExample(example.fact, example.previous_fact,
                                                           filtered_making_up_tests, filtered_logical_constraints,
                                                           filtered_subject_paraphrasing_tests, filtered_two_hop_tests,
                                                           filtered_prev_storage_tests))

    print(f'Filtered dataset has {len(filtered_examples)} / {len(dataset.examples)} examples')
    print(f'Filtered dataset has {filtered_test_count} / {test_count} tests')
    print('Saving filtered dataset')
    filtered_dataset = Dataset(filtered_examples)
    filtered_dataset.to_file(args.output)

    print('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('benchmark', help='The benchmark file path')
    parser.add_argument('model', help='The model name', choices=['gpt2-medium', 'gpt2-large', 'gpt2-xl',
                                                                 'gpt-j', 'gpt-neox',
                                                                 'llama-7b', 'llama-13b',
                                                                 'gpt-3'])
    parser.add_argument('output', help='The output filtered benchmark file path')
    parser.add_argument('--include-all-facts', action=argparse.BooleanOptionalAction, default=True,
                        help='Whether to include all facts or only facts that pass the known/unknown test')

    main(parser.parse_args())
