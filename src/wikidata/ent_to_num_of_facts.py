import json
import os
from collections import defaultdict
from config import checkable_relations, interesting_relations


def get_subject2num_of_facts(wikidata_dir: str):
    relevant_files = []
    for file in os.listdir(wikidata_dir):
        if file[-5:] == '.json':
            relevant_files.append(os.path.join(wikidata_dir, file))

    result_dict = defaultdict(int)
    for path in relevant_files:
        with open(path, 'r+', encoding='utf-8') as f:
            curr_part = json.load(f)
        for subject, facts in curr_part.items():
            interesting_facts = [fact for fact in facts if fact[0] in interesting_relations]
            result_dict[subject] = len(interesting_facts)

    return result_dict


if __name__ == '__main__':
    wikidata_dir = './wikidata_full_kg/filtered_relations'
    subject2num_of_facts = get_subject2num_of_facts(wikidata_dir)
    with open('./subject2num_of_facts.json', 'w+', encoding='utf-8') as f:
        json.dump(subject2num_of_facts, f)
    print(len(subject2num_of_facts))
