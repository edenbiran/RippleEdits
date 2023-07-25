import json
import os
import numpy as np
import random
from utils import load_json, write_json, ent_label2id, is_relation_associated, is_relations_associated, \
    subject_relation_to_targets, retrieve_from_wikidata
from config import checkable_relations
from collections import defaultdict
from relations import our_relations


def ent_and_num_of_facts_lists():
    ent2num_of_facts = load_json('./subject2num_of_facts.json')
    num_of_ents = len(ent2num_of_facts)
    ents_list, num_of_facts_list = [None for _ in range(num_of_ents)], np.zeros(num_of_ents)

    i = 0
    for ent, num_of_facts in ent2num_of_facts.items():
        ents_list[i], num_of_facts_list[i] = ent, num_of_facts
        i += 1

    return ents_list, num_of_facts_list


def ent_and_num_of_facts_lists_filtered():
    ent2num_of_facts = load_json('./subject2num_of_facts.json')
    sampled_ents = random.sample(list(ent2num_of_facts.items()), 200000)
    filtered_ent2num_of_facts = dict()
    i = 0
    for ent, num_of_facts in sampled_ents:
        i += 1
        if is_interesting_ent(ent):
            filtered_ent2num_of_facts[ent] = num_of_facts
        if i % 100 == 0:
            print(f'{i}/{len(sampled_ents)}')
    num_of_ents = len(filtered_ent2num_of_facts)
    ents_list, num_of_facts_list = [None for _ in range(num_of_ents)], np.zeros(num_of_ents)

    i = 0
    for ent, num_of_facts in filtered_ent2num_of_facts.items():
        ents_list[i], num_of_facts_list[i] = ent, num_of_facts
        i += 1

    # return ents_list, num_of_facts_list
    print(f'Number of remained entities is {len(filtered_ent2num_of_facts)}')
    return filtered_ent2num_of_facts


def ent_and_num_of_facts_lists_filtered2():
    ent2num_of_facts = load_json('./subject2num_of_facts.json')
    sampled_ents = random.sample(list(ent2num_of_facts.items()), 10000)
    filtered_ent2num_of_facts = dict()
    i = 0
    for ent, num_of_facts in sampled_ents:
        i += 1
        if is_interesting_ent2(ent):
            filtered_ent2num_of_facts[ent] = num_of_facts
        if i % 100 == 0:
            print(f'{i}/{len(sampled_ents)}')
    num_of_ents = len(filtered_ent2num_of_facts)
    ents_list, num_of_facts_list = [None for _ in range(num_of_ents)], np.zeros(num_of_ents)

    i = 0
    for ent, num_of_facts in filtered_ent2num_of_facts.items():
        ents_list[i], num_of_facts_list[i] = ent, num_of_facts
        i += 1

    return ents_list, num_of_facts_list


def is_interesting_ent(ent_label: str):
    ent_id = ent_label2id(ent_label)
    relation_ids = [relation_id for relation_name, relation_id in our_relations.items()]
    if is_relations_associated(ent_id, relation_ids):
        return True
    return False


def is_interesting_ent2(ent_label: str):
    ent_facts = retrieve_from_wikidata(ent_label, './wikidata_full_kg/filtered_relations')
    if ent_facts is None:
        return False
    our_relations_list = list(our_relations.keys())
    for relation, target in ent_facts:
        if any([relation == our_relation for our_relation in our_relations_list]):
            return True
    return False


def top_k_most_popular_subjects(k: int):
    ents_list, num_of_facts_list = ent_and_num_of_facts_lists_filtered()
    top_k_idx = np.argpartition(num_of_facts_list, -k)[-k:]
    top_k_ents = [ents_list[i] for i in top_k_idx]
    return top_k_ents


def divide_ents_per_popularity(num_of_divisions: int):
    # ents_list, num_of_facts_list = ent_and_num_of_facts_lists_filtered()
    ents_list, num_of_facts_list = ent_and_num_of_facts_lists()
    size_of_each_division = len(ents_list) // num_of_divisions
    sorted_idx = np.argsort(-num_of_facts_list)
    idx_groups = []
    for i in range(1, num_of_divisions + 1):
        idx_groups.append(sorted_idx[(i-1) * size_of_each_division: i * size_of_each_division])
    ent_groups = [[ents_list[i] for i in current_idx_group] for current_idx_group in idx_groups]
    return ent_groups


def sample_ents_according_to_popularity(num_of_divisions: int, amount_from_each_popularity: list):
    assert num_of_divisions == len(amount_from_each_popularity)
    ents_divided_per_popularity = divide_ents_per_popularity(num_of_divisions)
    grouped_samples = [random.sample(ents_divided_per_popularity[i],
                                     min(amount_from_each_popularity[i], len(ents_divided_per_popularity[i])))
                       for i in range(num_of_divisions)]
    return grouped_samples


def wikidata_subset(ents: list, wikidata_dir: str):
    relevant_files = []
    for file in os.listdir(wikidata_dir):
        if file[-5:] == '.json':
            relevant_files.append(os.path.join(wikidata_dir, file))

    result_dict = defaultdict(list)
    for path in relevant_files:
        curr_part = load_json(path)
        for ent in ents:
            if ent in curr_part:
                facts = curr_part[ent]
                result_dict[ent].extend(facts)

    return result_dict


def sample_fact_given_subject(subject_label: str):
    subject_id = ent_label2id(subject_label)
    if subject_id is None:
        return ()
    relations = list(our_relations.keys())
    for relation in relations:
        relation_id = our_relations[relation]
        targets = subject_relation_to_targets(subject_id, relation_id)
        if targets:
            return subject_id, relation, random.sample(targets, 1)[0]


def sample_k_facts(k: int, wikidata: dict):
    checkable_ents = []
    for ent, facts in wikidata.items():
        for relation, target in facts:
            if relation in checkable_relations:
                checkable_ents.append(ent)

    sampled_ents = random.sample(checkable_ents, min(len(checkable_ents), k))
    sampled_facts = []
    for ent in sampled_ents:
        facts = wikidata[ent]
        checkable_facts = [fact for fact in facts if fact[0] in checkable_relations]
        random_fact = random.sample(checkable_facts, 1)[0]
        sampled_facts.append((ent, random_fact))

    return sampled_facts


def union_per_dividers(data, dividers):
    new_data = []
    for i in range(1, len(dividers)):
        prev_div = dividers[i-1]
        curr_div = dividers[i]
        curr_group = []
        for j in range(prev_div, curr_div):
            curr_group.extend(data[j])
        new_data.append(curr_group)
    return new_data


if __name__ == '__main__':
    # filtered_ent2num_of_facts = ent_and_num_of_facts_lists_filtered()
    # write_json(filtered_ent2num_of_facts, './filtered_ent2num_of_facts.json')

    wikidata_dir = './wikidata_full_kg/filtered_relations'
    grouped_ents = sample_ents_according_to_popularity(20, [300000 for _ in range(20)])
    print('have done with dividing to buckets')
    print('start filtering...')
    interesting_dividers = [0, 2, 5, 9, 15]
    new_groups_division = union_per_dividers(grouped_ents, interesting_dividers)
    how_many_from_each = 5000
    filtered_group_ents = []
    for i, current_full_group in enumerate(new_groups_division):
        current_group = []
        print(f'start filtering group {i+1}. Its size is {len(current_full_group)}')
        random.shuffle(current_full_group)
        for entity in current_full_group:
            if is_interesting_ent(entity):
                current_group.append(entity)
                if len(current_group) % 10 == 0:
                    print(f'{len(current_group)}/{how_many_from_each}')
            if len(current_group) > how_many_from_each:
                break
        filtered_group_ents.append(current_group)
        print(f'done with bucket {i+1}')
    write_json(filtered_group_ents, f'../generations/sampled_entities_divided_to_buckets_{how_many_from_each}.json')

    facts = []
    for group in filtered_group_ents:
        sampled_facts = [list(sample_fact_given_subject(subject)) for subject in group if subject is not None]
        facts.append(sampled_facts)
    # sampled_facts = [list(sample_fact_given_subject(subject)) for subject in sampled_ents]
    write_json(facts, f'../generations/sampled_facts_divided_to_buckets{how_many_from_each}_.json')
    # print(f'{len(sampled_facts)} facts were sampled')
    # print(f'Examples: {random.sample(sampled_facts), 10}')


