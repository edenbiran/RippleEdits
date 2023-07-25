from wikidata.relations import our_relations, relation2impacted_relations, relation2phrase
from wikidata.utils import subject_relation_to_targets, ent_to_relation_ids, get_label, get_aliases, get_description, \
    subjects_given_relation_target
from build_logical_constraints import generate_constraints
from utils import create_test_example_given_input_targets
from relation import Relation
from query import Query, TwoHopQuery
from testcase import TestCase
from two_hop_phrases import relation_couple_to_phrase


def making_up_axis(subject_id: str, relation: Relation):
    tests = []

    if relation not in Relation:
        return tests

    impacted_relations = relation.impacted_relations()
    for other_relation in Relation:
        if other_relation == relation or other_relation in impacted_relations:
            continue
        corresponding_targets = subject_relation_to_targets(subject_id, other_relation)
        if not corresponding_targets:
            continue
        test_query = Query(subject_id, other_relation, corresponding_targets)
        condition_queries = [test_query]
        tests.append(TestCase(test_query=test_query, condition_queries=condition_queries))

    return tests


def logical_constraints_axis(subject_id: str, relation: Relation, target_id: str):
    return generate_constraints(subject_id, relation, target_id)


def subject_aliasing_axis(subject_id: str, relation: Relation, target_id: str):
    tests = []
    subject_aliases = get_aliases(subject_id)
    for alias in subject_aliases:
        phrase = relation.phrase(alias)
        test_query = Query(subject_id, relation, target_id, phrase)
        condition_queries = [test_query]
        tests.append(TestCase(test_query=test_query, condition_queries=condition_queries))
    return tests


def two_hop_axis(subject_id: str, relation: Relation, target_id: str):
    tests = []
    if not target_id or target_id[0] != 'Q':
        return tests
    target_relations = ent_to_relation_ids(target_id)
    for relation_id in target_relations:
        second_relation_enum = Relation.id_to_enum(relation_id)
        if second_relation_enum is None:
            continue
        second_hop_targets = subject_relation_to_targets(target_id, second_relation_enum)
        for second_hop_target in second_hop_targets:
            phrase = relation_couple_to_phrase(relation, second_relation_enum)
            if phrase is None:
                continue
            phrase = phrase.replace('<subject>', get_label(subject_id))
            test_query = TwoHopQuery(subject_id, relation, target_id, second_relation_enum, second_hop_target, phrase)
            condition_queries = [Query(target_id, second_relation_enum, second_hop_target)]
            tests.append(TestCase(test_query=test_query, condition_queries=condition_queries))
    return tests


def forward_two_hop_axis(subject_id: str, relation: Relation, target_id: str):
    tests = []
    if not target_id or target_id[0] != 'Q':
        return tests
    for backward_relation in Relation:
        backward_relation_id = backward_relation.id()
        backward_subjects = subjects_given_relation_target(backward_relation_id, subject_id)
        for backward_subject in backward_subjects:
            phrase = relation_couple_to_phrase(backward_relation, relation)
            if phrase is None:
                continue
            phrase = phrase.replace('<subject>', get_label(backward_subject))
            test_query = TwoHopQuery(backward_subject, backward_relation, subject_id, relation, target_id, phrase)
            condition_queries = [Query(backward_subject, backward_relation, subject_id)]
            tests.append(TestCase(test_query=test_query, condition_queries=condition_queries))
    return tests


# def temporal_axis(subject_id: str, relation: Relation, previous_target_id: str):
#     tests = []
#     if relation.is_modification():
#         return tests
#     test_query = Query(subject_id, relation, previous_target_id)
#     condition_queries = [test_query]
#     tests.append(TestCase(test_query=test_query, condition_queries=condition_queries))
#     return tests

def temporal_axis(subject_id: str, relation: Relation, target_id: str):
    tests = []
    if relation.is_modification():
        return tests
    wikidata_targets = subject_relation_to_targets(subject_id, relation)
    relational_phrase = relation.phrase(get_label(subject_id))
    if 'is' in relational_phrase:
        prefix = relational_phrase[:-3]
    elif 'are' in relational_phrase:
        prefix = relational_phrase[:-4]
    phrase = prefix + f', which is not {get_label(target_id)}, is'
    test_query = Query(subject_id, relation, wikidata_targets, phrase=phrase)
    condition_queries = [test_query]
    tests.append(TestCase(test_query=test_query, condition_queries=condition_queries))
    return tests


# for test in subject_aliasing_axis('Q42', 'occupation', 'Q36834'):
#     print(test)


