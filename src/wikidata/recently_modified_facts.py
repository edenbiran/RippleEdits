import sys
import random
from wikidata.relations import our_relations
from wikidata.utils import write_json
from qwikidata.sparql import (get_subclasses_of_item,
                              return_sparql_query_results)
from qwikidata.json_dump import WikidataJsonDump
from qwikidata.utils import dump_entities_to_json
from qwikidata.entity import WikidataItem, WikidataLexeme, WikidataProperty
from qwikidata.linked_data_interface import get_entity_dict_from_api


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


def recently_modified_facts_given_relation(relation_id: str, k_recent_days: int = 7, limit: int = 100):
    sparql_query = f"""
    SELECT DISTINCT ?item ?target ?date_modified
    WHERE
    {{
      ?item wdt:{relation_id} ?target ;
              schema:dateModified ?date_modified .
        BIND (now() - ?date_modified as ?date_range)
        FILTER (?date_range < {k_recent_days + 1})
      
        SERVICE wikibase:label {{
          bd:serviceParam wikibase:language "en" .
         }}
    }}
    LIMIT {limit}
    """

    res = return_sparql_query_results(sparql_query)
    return sparkql_res_to_list_of_facts(res, relation_id)


def specific_dates_range_modified_facts_given_relation(
        relation_id: str,
        start_in_days_ago: int = 0,
        end_in_days_ago: int = 1,
        limit: int = 100
):
    sparql_query = f"""
    SELECT DISTINCT ?item ?target ?date_modified
    WHERE
    {{
      ?item wdt:{relation_id} ?target ;
              schema:dateModified ?date_modified .
        BIND (now() - ?date_modified as ?date_range)
        FILTER (?date_range >= {start_in_days_ago} && ?date_range < {end_in_days_ago})

        SERVICE wikibase:label {{
          bd:serviceParam wikibase:language "en" .
         }}
    }}
    LIMIT {limit}
    """

    try:
        res = return_sparql_query_results(sparql_query)
    except:
        return []
    return sparkql_res_to_list_of_facts(res, relation_id)


def sample_uniformly_from_recent_days(relation_id: str, k_recent_days: int = 120, amount_from_each_day: int = 1):
    facts = []
    for i in range(k_recent_days):
        current_possible_facts = specific_dates_range_modified_facts_given_relation(
            relation_id, start_in_days_ago=i, end_in_days_ago=i+1, limit=100
        )
        facts.extend(random.sample(current_possible_facts, min(amount_from_each_day, len(current_possible_facts))))
    return facts


def construct_uniformly_from_recent_days_recently_modified_dataset(k_recent_days: int = 120,
                                                                   amount_from_each_day: int = 1):
    dataset = []
    for relation_name, relation_id in our_relations.items():
        print(f'Processing {relation_name}...')
        dataset.extend(sample_uniformly_from_recent_days(relation_id, k_recent_days, amount_from_each_day))
    return dataset


if __name__ == '__main__':
    dataset = construct_uniformly_from_recent_days_recently_modified_dataset(k_recent_days=250, amount_from_each_day=4)
    print(len(dataset))
    write_json(dataset, '../generations/uniformly_from_recent_days_recently_modified_dataset.json')
