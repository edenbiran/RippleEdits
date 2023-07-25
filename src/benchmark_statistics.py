import argparse

import numpy as np
import pandas as pd
import wptools
import functools
from tqdm import tqdm
import matplotlib.pyplot as plt

from benchmark import Dataset


plt.rcParams.update({'text.usetex': True})
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({'figure.figsize': (14, 3)})


@functools.lru_cache()
def get_entity_info(entity, is_id=True):
    claim_count = None
    backlinks = None
    views = None

    try:
        if is_id:
            page = wptools.page(wikibase=entity, silent=True)
        else:
            page = wptools.page(entity, silent=True)
        page.REQUEST_LIMIT = 500
        page.get_wikidata()
        claim_count = sum([len(values) for _, values in page.data['claims'].items()])
        page.get_more()
        backlinks = len(page.data['backlinks'])
        views = page.data['views']
    except (LookupError, StopIteration) as e:
        print(f'Error looking up {entity}: {e}')

    return claim_count, backlinks, views


def get_axis_stats(tests):
    test_count = len(tests)
    test_query_count = 0
    condition_query_count = 0
    for testcase in tests:
        test_query_count += len(testcase.get_test_queries())
        condition_query_count += len(testcase.get_condition_queries())
    return test_count, test_query_count, condition_query_count


def get_example_stats(example):
    example_type = type(example).__name__

    subject_id = example.fact._subject_id
    subject_claim_count, subject_backlinks, subject_views = get_entity_info(subject_id)

    target_id = example.fact._target_id
    target_claim_count, target_backlinks, target_views = get_entity_info(target_id)

    relation = example.fact._relation.name

    axis_stats = [
        get_axis_stats(example.making_up_tests),
        get_axis_stats(example.logical_constraints),
        get_axis_stats(example.subject_paraphrasing_tests),
        get_axis_stats(example.two_hop_tests),
        get_axis_stats(example.forward_two_hop_tests),
        get_axis_stats(example.prev_storage_tests)
    ]
    test_count, test_query_count, condition_query_count = (sum(x) for x in zip(*axis_stats))

    return {
        'example_type': example_type,

        'subject_id': subject_id,
        'subject_claim_count': subject_claim_count,
        'subject_backlinks': subject_backlinks,
        'subject_views': subject_views,

        'target_id': target_id,
        'target_claim_count': target_claim_count,
        'target_backlinks': target_backlinks,
        'target_views': target_views,

        'relation': relation,

        'test_count': test_count,
        'test_query_count': test_query_count,
        'condition_query_count': condition_query_count
    }


def relation_counts_to_axis(counts):
    return [s.replace('_', ' ').lower() for s in counts.index], counts.values * 100


def display_statistics(dfs, args):
    for df in dfs:
        df['avg_conditions_per_test'] = df['condition_query_count'] / df['test_count']
        print('Statistics:')
        print(df.describe().to_string())
        print('--------------------------')

        print('Relations:')
        print(df['relation'].value_counts(normalize=True))

    if args.plot:
        fig, axes = plt.subplots(1, len(dfs), sharey=True)
        for i, (ax, df, title) in enumerate(zip(axes, dfs, args.titles)):
            x, y = relation_counts_to_axis(df['relation'].value_counts(normalize=True)[:10])
            ax.bar(x, y)
            start, end = ax.get_ylim()
            ax.yaxis.set_ticks(np.arange(start, end, 5))
            ax.set_xticklabels(x, rotation=60, ha='right', rotation_mode='anchor')
            ax.set_title('\\textsc{%s}' % title)
            if i == 0:
                ax.set_ylabel('\% of edits')
        fig.savefig(args.plot, bbox_inches='tight')


def main(args):
    if args.benchmark:
        print(f'Loading benchmark from {args.benchmark}')
        dataset = Dataset.from_file(args.benchmark)

        print('Collecting statistics')
        stats = []
        for example in tqdm(dataset.examples):
            stats.append(get_example_stats(example))
        stats_df = pd.DataFrame(stats)

        if not args.statistics:
            args.statistics = 'statistics.json'
        print(f'Saving statistics to {args.statistics}')
        stats_df.to_json(args.statistics)
        stats_dfs = [stats_df]

    elif args.statistics:
        print(f'Loading statistics from {args.statistics}')
        stats_dfs = [pd.read_json(s) for s in args.statistics]

    else:
        raise Exception('Wrong arguments given')

    display_statistics(stats_dfs, args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--benchmark', help='The benchmark file path')
    parser.add_argument('-s', '--statistics', nargs='*', help='The statistics file paths. '
                                                              'One path if output, multiple if input.')
    parser.add_argument('-p', '--plot', help='The relations plot file path')
    parser.add_argument('-t', '--titles', nargs='*', help='The relations plot titles')
    main(parser.parse_args())
