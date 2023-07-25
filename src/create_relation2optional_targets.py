import json
import os
import random
from collections import defaultdict
from relation import Relation


checkable_relations = [relation.formal_name() for relation in Relation]


def get_relation2optional_targets(wikidata_dir: str):
    relevant_files = []
    for file in os.listdir(wikidata_dir):
        if file[-5:] == '.json':
            relevant_files.append(os.path.join(wikidata_dir, file))

    result_dict = defaultdict(set)
    for i, path in enumerate(relevant_files):
        print(f'{i+1}/{len(relevant_files)}')
        with open(path, 'r+', encoding='utf-8') as f:
            curr_part = json.load(f)
        for subject, facts in curr_part.items():
            for relation, target in facts:
                if relation in checkable_relations and len(result_dict[relation]) < 100000:
                    result_dict[relation].add(target)

    result_dict = {relation: list(targets) for relation, targets in result_dict.items()}
    return result_dict


if __name__ == '__main__':
    wikidata_dir = './wikidata/wikidata_full_kg/filtered_relations'
    relation2optional_targets = get_relation2optional_targets(wikidata_dir)
    with open('./wikidata/relation2optional_targets_new_limited.json', 'w+', encoding='utf-8') as f:
        json.dump(relation2optional_targets, f)
    print(relation2optional_targets.keys())
    print(len(relation2optional_targets))