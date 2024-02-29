import json
import csv
import os
import functools
from collections import defaultdict
from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.entity import WikidataItem
from qwikidata.sparql import return_sparql_query_results
import zipfile


def load_json(path: str):
    with open(path, 'r+', encoding='utf-8') as f:
        result = json.load(f)
    return result


def write_json(d: dict, path: str):
    with open(path, 'w+', encoding='utf-8') as f:
        json.dump(d, f)


def add_to_json(d, path):
    with open(path, 'r+', encoding='utf-8') as f:
        curr_data = json.load(f)
    if isinstance(curr_data, list):
        new_data = curr_data + d
    elif isinstance(curr_data, dict):
        curr_data.update(d)
    with open(path, 'w+', encoding='utf-8') as f:
        json.dump(new_data, f)


def write_to_csv(path: str, table: list):
    with open(path, 'a+', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        for line in table:
            csv_writer.writerow(line)


def read_from_csv(path: str):
    table = []
    with open(path, 'r+', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for line in csv_reader:
            table.append(line)
    return table


def retrieve_from_wikidata(ent: str, wikidata_dir: str = './wikidata_full_kg/filtered_relations'):
    if not ent:
        return None
    relevant_files = []
    for file in os.listdir(wikidata_dir):
        if file[-5:] == '.json':
            relevant_files.append(os.path.join(wikidata_dir, file))

    for path in relevant_files:
        curr_part = load_json(path)
        if ent in curr_part:
            return curr_part[ent]
    return None


def facts_list_to_relation2targets(facts: list):
    relation2targets = defaultdict(list)
    for relation, target in facts:
        relation2targets[relation].append(target)
    return relation2targets


@functools.lru_cache()
def wikidata_item_given_id(ent_id: str):
    try:
        return WikidataItem(get_entity_dict_from_api(ent_id))
    except:
        return None


def get_label(ent_id: str):
    if isinstance(ent_id, list):
        if len(ent_id) > 0:
            ent_id = ent_id[0]
        else:
            return ent_id
    if ent_id[0] != 'Q':
        return ent_id
    item = wikidata_item_given_id(ent_id)
    if item is not None:
        label = item.get_label()
    else:
        return ent_id
    if label is None:
        return ent_id
    return label


def get_aliases(ent_id: str):
    item = wikidata_item_given_id(ent_id)
    if item is not None:
        return item.get_aliases()
    return [ent_id]


def get_description(ent_id: str):
    item = wikidata_item_given_id(ent_id)
    if item is not None:
        return item.get_description()
    return [ent_id]


def get_targets_given_item_and_relation(item: WikidataItem, relation_id: str):
    related_claims = item.get_truthy_claim_groups()
    if relation_id not in related_claims:
        return []
    curr_relation_claims = related_claims[relation_id]
    try:
        target_ids = [claim.mainsnak.datavalue.value["id"] for claim in curr_relation_claims]
        return target_ids
    except:
        return []


def is_relation_associated(ent_id, relation_id):
    try:
        ent_item = wikidata_item_given_id(ent_id)
    except:
        return False
    return len(get_targets_given_item_and_relation(ent_item, relation_id)) > 0


def is_relations_associated(ent_id, relation_ids: list):
    try:
        ent_item = wikidata_item_given_id(ent_id)
    except:
        return False
    related_claims = ent_item.get_truthy_claim_groups()
    for relation_id in relation_ids:
        if relation_id in related_claims:
            return True
    return False


def subject_relation_to_targets(subject_id: str, relation):
    if not isinstance(relation, str):
        relation_id = relation.id()
    else:
        relation_id = relation
    subject_item = wikidata_item_given_id(subject_id)
    return get_targets_given_item_and_relation(subject_item, relation_id)


def ent_to_relation_ids(ent_id: str):
    item = wikidata_item_given_id(ent_id)
    if item is None:
        return []
    related_claims = item.get_truthy_claim_groups()
    return list(related_claims.keys())


with zipfile.ZipFile('./wikidata/ent_label2id.json.zip', 'r') as zip_ref:
    zip_ref.extractall('./wikidata/ent_label2id.json')

ent_label2id_dict = load_json('./wikidata/ent_label2id.json')


def ent_label2id(label: str):
    if label not in ent_label2id_dict:
        return None
    return ent_label2id_dict[label]


def extract_ent_id_from_url(url: str):
    pointer = len(url) - 1
    while url[pointer] != '/':
        pointer -= 1
    return url[pointer+1:]


def sparkql_res_to_list_of_facts(sparkql_res: dict, relation_id: str):
    resulted_facts = []
    for returned_fact in sparkql_res['results']['bindings']:
        subject, target = returned_fact['item'], returned_fact['target']

        # handling subject
        if subject['type'] == 'uri':
            subject = extract_ent_id_from_url(subject['value'])
        elif subject['type'] == 'literal':
            subject = subject['value']

        # handling target
        if target['type'] == 'uri':
            target = extract_ent_id_from_url(target['value'])
        elif target['type'] == 'literal':
            target = target['value']

        resulted_facts.append((subject, relation_id, target))

    return resulted_facts


def sparkql_res_to_list_of_entities(sparkql_res: dict):
    resulted_entities = []
    for returned_ent in sparkql_res['results']['bindings']:
        subject = returned_ent['itemLabel']

        # handling subject
        if subject['type'] == 'uri':
            subject = extract_ent_id_from_url(subject['value'])
        elif subject['type'] == 'literal':
            subject = subject['value']

        resulted_entities.append(subject)

    return resulted_entities


def subjects_given_relation_target(relation_id: str, target_id: str, limit: int = 10):
    sparql_query = f"""
    SELECT DISTINCT ?item ?itemLabel 
    WHERE
    {{
      ?item wdt:{relation_id} wd:{target_id};
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }}
    }}
    LIMIT {limit}
    """

    try:
        res = return_sparql_query_results(sparql_query)
        return sparkql_res_to_list_of_entities(res)
    except:
        return []

