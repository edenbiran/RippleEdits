import json
import os
import random
from collections import defaultdict
from config import checkable_relations


def get_relation2optional_targets(wikidata_dir: str):
    relevant_files = []
    for file in os.listdir(wikidata_dir):
        if file[-5:] == '.json':
            relevant_files.append(os.path.join(wikidata_dir, file))

    result_dict = defaultdict(set)
    for path in relevant_files:
        with open(path, 'r+', encoding='utf-8') as f:
            curr_part = json.load(f)
        for subject, facts in curr_part.items():
            for relation, target in facts:
                if relation in checkable_relations:
                    result_dict[relation].add(target)

    result_dict = {relation: list(targets) for relation, targets in result_dict.items()}
    return result_dict


if __name__ == '__main__':
    wikidata_dir = './wikidata_full_kg/filtered_relations'
    relation2optional_targets = get_relation2optional_targets(wikidata_dir)
    with open('./relation2optional_targets_new.json', 'w+', encoding='utf-8') as f:
        json.dump(relation2optional_targets, f)
    print(relation2optional_targets.keys())
    print(len(relation2optional_targets))