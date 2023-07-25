from collections import defaultdict

from benchmark import Dataset, Example, TestsAxis
from modeleditor import ROMEModelEditor, InContextModelEditor, MENDModelEditor, MEMITModelEditor
from queryexecutor import GPT2QueryExecutor, GPT3QueryExecutor, GPTJQueryExecutor, GPTNeoXQueryExecutor, \
    LlamaQueryExecutor
from testrunner import ExampleResult
from testrunner import TestRunner, TestResult
from wikidata.utils import write_json


class Evaluator:

    def __init__(self, query_executor, model_editor):
        self._query_executor = query_executor
        self._model_editor = model_editor
        self._test_runner = TestRunner(query_executor, model_editor)

    def average_acc(self, example: Example, test_cases: list, skip_edit: bool = False, skip_restore: bool = False):
        if not len(test_cases) and skip_edit:
            return 0.0, 0.0, 0.0, False

        run_res = self._test_runner.run_testcases(example, test_cases, skip_edit=skip_edit, skip_restore=skip_restore)
        fact_edit_succeeded, res_dict = run_res
        edit_succeeded = True
        if fact_edit_succeeded == ExampleResult.EDIT_FAILED:
            edit_succeeded = False

        if not len(test_cases):
            return 0.0, 0.0, 0.0, edit_succeeded

        werent_executed = len(res_dict[TestResult.NOT_EXECUTED])
        successes = len(res_dict[TestResult.PASSED])
        fails = len(res_dict[TestResult.FAILED])
        executed = (successes + fails) / (successes + fails + werent_executed)
        return successes / (successes + fails) if successes else 0.0, executed, len(test_cases), edit_succeeded

    def evaluate_making_up_axis(self, example: Example):
        return self.average_acc(example, example.making_up_tests, skip_restore=True)

    def evaluate_logical_constraints(self, example: Example):
        return self.average_acc(example, example.logical_constraints, skip_edit=True, skip_restore=True)

    def evaluate_subject_paraphrasing(self, example: Example):
        return self.average_acc(example, example.subject_paraphrasing_tests, skip_edit=True, skip_restore=True)

    def evaluate_two_hop_tests(self, example: Example):
        return self.average_acc(example, example.two_hop_tests, skip_edit=True, skip_restore=True)

    def evaluate_forward_two_hop_tests(self, example: Example):
        return self.average_acc(example, example.forward_two_hop_tests, skip_edit=True, skip_restore=True)

    def evaluate_prev_storage_tests(self, example: Example):
        return self.average_acc(example, example.prev_storage_tests, skip_edit=True, skip_restore=False)

    def evaluate(self, example: Example):
        res = defaultdict()
        res[TestsAxis.MAKING_UP] = self.evaluate_making_up_axis(example)
        res[TestsAxis.LOGICAL_CONSTRAINTS] = self.evaluate_logical_constraints(example)
        res[TestsAxis.SUBJECT_PARAPHRASING] = self.evaluate_subject_paraphrasing(example)
        res[TestsAxis.TWO_HOP] = self.evaluate_two_hop_tests(example)
        res[TestsAxis.FORWARD_TWO_HOP] = self.evaluate_forward_two_hop_tests(example)
        res[TestsAxis.PREVIOUS_STORAGE] = self.evaluate_prev_storage_tests(example)
        return res


class ConditionsEvaluator(Evaluator):

    def __init__(self, query_executor):
        super(ConditionsEvaluator, self).__init__(query_executor, None)


if __name__ == '__main__':
    models = [
        'gpt2-medium',
        'gpt2-large',
        'gpt2-xl',
        'gpt-j',
        'gpt-neo',
        'llama'
    ]

    editors = [
        'mend',
        'rome',
        'memit',
        'in-context'
    ]

    recently_modified_path = '../data/benchmark/recent.json'
    fake_facts_path = '../data/benchmark/random.json'
    top_views_path = '../data/benchmark/popular.json'

    datasets = [
        recently_modified_path,
        fake_facts_path,
        top_views_path
    ]

    for model in models:
        for editor in editors:
            for dataset_path in datasets:

                if dataset_path == recently_modified_path:
                    dataset_name = 'recently_modified'
                if dataset_path == fake_facts_path:
                    dataset_name = 'fake_facts'
                if dataset_path == top_views_path:
                    dataset_name = 'top_views'

                experiment_name = f'{model}_{editor}_{dataset_name}'
                print(experiment_name)

                davinvci_query_executor = GPT3QueryExecutor(model_size='text-davinci-003')
                if model == 'gpt2-medium':
                    query_executor = GPT2QueryExecutor('medium')
                if model == 'gpt2-large':
                    query_executor = GPT2QueryExecutor('large')
                if model == 'gpt2-xl':
                    query_executor = GPT2QueryExecutor('xl')
                if model == 'gpt-j':
                    query_executor = GPTJQueryExecutor()
                if model == 'gpt-neo':
                    query_executor = GPTNeoXQueryExecutor()
                if model == 'llama':
                    query_executor = LlamaQueryExecutor()

                if editor == 'mend':
                    model_editor = MENDModelEditor(query_executor)
                if editor == 'rome':
                    model_editor = ROMEModelEditor(query_executor)
                if editor == 'memit':
                    model_editor = MEMITModelEditor(query_executor)
                if editor == 'in-context':
                    model_editor = InContextModelEditor(query_executor)

                evaluator = Evaluator(query_executor=query_executor, model_editor=model_editor)
                dataset = Dataset.from_file(dataset_path)

                precisions_json = dict()
                num_of_examples = 200

                examples_for_eval = dataset.sample(num_of_examples)
                eval_size = len(examples_for_eval)

                succeeded_edits = defaultdict(lambda: 0)
                average_precision = defaultdict(lambda: 0)
                average_executed = defaultdict(lambda: 0)
                average_size = defaultdict(lambda: 0)
                total_checked_examples = defaultdict(lambda: 0)
                executed_portion_dict = defaultdict(lambda: 0)

                for i, example in enumerate(examples_for_eval):
                    if (i + 1) % 10 == 0:
                        print(f'{i + 1}/{eval_size}')

                    if example.fact.get_subject_label() == '' or example.fact.get_target_label() == '':
                        print(f'Skipping example: {example.to_dict()}')
                        continue

                    evaluation_results = evaluator.evaluate(example)

                    res_dict_for_json = dict()
                    for axis, results in evaluation_results.items():
                        precision, executed, size, edit_succeeded = results
                        if executed == 0.0:
                            continue
                        if edit_succeeded:
                            succeeded_edits[axis] += 1
                        average_precision[axis] += precision
                        res_dict_for_json[axis.name] = precision
                        average_executed[axis] += executed
                        average_size[axis] += size
                        # precisions_json[str(example.fact)] = precision
                        total_checked_examples[axis] += 1

                    precisions_json[str(example.fact)] = res_dict_for_json

                    for axis in TestsAxis:
                        if axis in evaluation_results:
                            executed_portion_dict[axis] += evaluation_results[axis][1]

                res_str = ''
                for axis in TestsAxis:
                    print(f'Results of axis {axis}:')
                    res_str += f'Results of axis {axis}:\n'

                    if total_checked_examples[axis] == 0:
                        print(f'No checked tests for this axis')
                        res_str += f'No checked tests for this axis\n'
                        continue

                    average_precision[axis] /= total_checked_examples[axis]
                    average_executed[axis] /= total_checked_examples[axis]
                    average_size[axis] /= total_checked_examples[axis]

                    print(f'{(succeeded_edits[axis] / eval_size) * 100} successful edits (out of {eval_size})')
                    res_str += f'{(succeeded_edits[axis] / eval_size) * 100} successful edits (out of {eval_size})\n'
                    print(f'Average accuracy is {average_precision[axis]}')
                    res_str += f'Average accuracy is {average_precision[axis]}\n'
                    print(f'Average portion of executed_tests is {average_executed[axis]}')
                    res_str += f'Average portion of executed_tests is {average_executed[axis]}\n'
                    print(f'Average total number of tests is {average_size[axis]}')
                    res_str += f'Average total number of tests is {average_size[axis]}\n'

                write_json(precisions_json, f'./{experiment_name}_res_2.json')

                with open(f'./{experiment_name}_2.txt', 'w+', encoding='utf-8') as f:
                    f.write(res_str)
