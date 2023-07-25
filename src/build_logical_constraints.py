import json
import os
from wikidata.utils import load_json, write_json, get_label, get_aliases, subject_relation_to_targets
from wikidata.relations import our_relations, relation2phrase
from utils import create_test_example_given_input_targets
from relation import Relation
from query import Query
from testcase import TestCase


class RelationalConstraints:

    def __init__(self, subject_id, edits={}):
        self.subject_id = subject_id
        self.edits = edits
        self.conditions = []

    def _targets(self, relation: Relation):
        targets = self.edits[relation] if relation in self.edits else subject_relation_to_targets(
            self.subject_id, relation)
        self.conditions.append(Query(self.subject_id, relation, targets))
        return targets

    def _edited_targets_only(self, relation: Relation):
        return self.edits[relation] if relation in self.edits else None

    def _targets_of(self, subject_ids, relation: Relation):
        targets = []
        if not isinstance(subject_ids, list):
            subject_ids = [subject_ids]
        for subject_id in subject_ids:
            targets += subject_relation_to_targets(subject_id, relation)
            self.conditions.append(Query(subject_id, relation, targets))
        return targets

    def empty_conditions(self):
        self.conditions = []

    def sibling(self):
        self.empty_conditions()
        mothers = self._targets(Relation.MOTHER)
        fathers = self._targets(Relation.FATHER)
        mother_children = self._targets_of(mothers, Relation.CHILD)
        father_children = self._targets_of(fathers, Relation.CHILD)
        return TestCase(
            test_query=Query(self.subject_id, Relation.SIBLING, mother_children + father_children),
            condition_queries=self.conditions
        )

    def sibling_of(self, ent_id: str):
        self.empty_conditions()
        mothers = self._targets_of(ent_id, Relation.MOTHER)
        fathers = self._targets(ent_id, Relation.FATHER)
        mother_children = self._targets_of(mothers, Relation.CHILD)
        father_children = self._targets_of(fathers, Relation.CHILD)
        return TestCase(
            test_query=Query(ent_id, Relation.SIBLING, mother_children + father_children),
            condition_queries=self.conditions
        )

    def mothers_child(self):
        mother = self._targets(Relation.MOTHER)

        if mother:
            mother = mother[0]
        else:
            return None

        return TestCase(
            test_query=Query(mother, Relation.CHILD, [self.subject_id]),
            condition_queries=[]
        )

    def fathers_child(self):
        father = self._targets(Relation.FATHER)
        if father:
            father = father[0]
        else:
            return None
        return TestCase(
            test_query=Query(father, Relation.CHILD, [self.subject_id]),
            condition_queries=[]
        )

    def sibling_of_new_sibling(self):
        new_sibling = self._edited_targets_only(Relation.BROTHER)
        if new_sibling is None:
            new_sibling = self._edited_targets_only(Relation.SISTER)
        if new_sibling is None:
            new_sibling = self._edited_targets_only(Relation.SIBLING)
        return TestCase(
            test_query=Query(new_sibling, Relation.SIBLING, [self.subject_id]),
            condition_queries=[]
        )

    def spouse_of_new_spouse(self):
        new_spouse = self._targets(Relation.SPOUSE)
        return TestCase(
            test_query=Query(new_spouse, Relation.SIBLING, [self.subject_id]),
            condition_queries=[]
        )

    def mothers_number_of_children(self):
        self.empty_conditions()
        mother = self._targets(Relation.MOTHER)

        if mother:
            mother = mother[0]
        else:
            return None

        num_children = len(self._targets_of([mother], Relation.CHILD))
        return TestCase(
            test_query=Query(mother, Relation.NUMBER_OF_CHILDREN, num_children + 1),
            condition_queries=self.conditions
        )

    def fathers_number_of_children(self):
        self.empty_conditions()
        father = self._targets(Relation.FATHER)

        if father:
            father = father[0]
        else:
            return None

        num_children = len(self._targets_of([father], Relation.CHILD))
        return TestCase(
            test_query=Query(father, Relation.NUMBER_OF_CHILDREN, num_children + 1),
            condition_queries=self.conditions
        )

    def mother_or_father_child(self):
        self.empty_conditions()
        mother = self._targets(Relation.MOTHER)
        if mother:
            mother = mother[0]
        else:
            return None
        father = self._targets(Relation.FATHER)[0]
        if father:
            father = father[0]
        else:
            return None

        new_sibling = self._edited_targets_only(Relation.SIBLING)
        if new_sibling is None:
            new_sibling = self._edited_targets_only(Relation.SISTER)
        if new_sibling is None:
            new_sibling = self._edited_targets_only(Relation.BROTHER)

        return TestCase(
            test_query=[Query(mother, Relation.CHILD, new_sibling), Query(father, Relation.CHILD, new_sibling)],
            condition_queries=self.conditions
        )

    def mother_or_father_of_new_sibling(self):
        self.empty_conditions()
        mother = self._targets(Relation.MOTHER)
        if mother:
            mother = mother[0]
        else:
            return None
        father = self._targets(Relation.FATHER)[0]
        if father:
            father = father[0]
        else:
            return None

        new_sibling = self._edited_targets_only(Relation.SIBLING)
        if new_sibling is None:
            new_sibling = self._edited_targets_only(Relation.SISTER)
        if new_sibling is None:
            new_sibling = self._edited_targets_only(Relation.BROTHER)

        return TestCase(
            test_query=[Query(new_sibling, Relation.MOTHER, mother), Query(new_sibling, Relation.FATHER, father)],
            condition_queries=self.conditions
        )


    def uncle(self):
        self.empty_conditions()
        mothers = self._targets(Relation.MOTHER)
        fathers = self._targets(Relation.FATHER)
        mother_siblings = self._targets_of(mothers, Relation.SIBLING)
        male_mother_siblings = [sibling for sibling in mother_siblings
                                if get_label(subject_relation_to_targets(sibling, Relation.SEX_OR_GENDER)[0]) == 'male']
        father_siblings = self._targets_of(fathers, Relation.SIBLING)
        male_father_siblings = [sibling for sibling in father_siblings
                                if get_label(subject_relation_to_targets(sibling, Relation.SEX_OR_GENDER)[0]) == 'male']
        return TestCase(
            test_query=Query(self.subject_id, Relation.UNCLE, male_mother_siblings + male_father_siblings),
            condition_queries=self.conditions
        )

    def aunt(self):
        self.empty_conditions()
        mothers = self._targets(Relation.MOTHER)
        fathers = self._targets(Relation.FATHER)
        mother_siblings = self._targets_of(mothers, Relation.SIBLING)
        female_mother_siblings = [sibling for sibling in mother_siblings
                                if get_label(subject_relation_to_targets(sibling, Relation.SEX_OR_GENDER)[0]) == 'female']
        father_siblings = self._targets_of(fathers, Relation.SIBLING)
        female_father_siblings = [sibling for sibling in father_siblings
                                if get_label(subject_relation_to_targets(sibling, Relation.SEX_OR_GENDER)[0]) == 'female']
        return TestCase(
            test_query=Query(self.subject_id, Relation.AUNT, female_mother_siblings + female_father_siblings),
            condition_queries=self.conditions
        )

    def is_dead_now(self):
        self.empty_conditions()
        is_alive_strs = ['yes', 'correct', 'true', 'is alive', 'is not dead']
        is_dead_strs = ['no', 'incorrect', 'false', 'is not alive', 'is dead']
        return TestCase(
            test_query=Query(self.subject_id, Relation.IS_ALIVE, is_dead_strs),
            condition_queries=self.conditions
        )

    def new_followed_by(self):
        self.empty_conditions()
        new_followed_one = self._edited_targets_only(Relation.FOLLOWS)
        return TestCase(
            test_query=Query(new_followed_one, Relation.FOLLOWED_BY, self.subject_id),
            condition_queries=self.conditions
        )

    def new_follows(self):
        self.empty_conditions()
        new_following_one = self._edited_targets_only(Relation.FOLLOWED_BY)
        return TestCase(
            test_query=Query(new_following_one, Relation.FOLLOWED_BY, self.subject_id),
            condition_queries=self.conditions
        )

    def continent(self):
        self.empty_conditions()
        country_associated_with = self._edited_targets_only(Relation.COUNTRY)
        if country_associated_with is None:
            country_associated_with = self._edited_targets_only(Relation.CAPITAL_OF)
        new_continent = self._targets_of(country_associated_with, Relation.CONTINENT)
        return TestCase(
            test_query=Query(self.subject_id, Relation.CONTINENT, new_continent),
            condition_queries=self.conditions
        )

    def currency(self):
        self.empty_conditions()
        country_associated_with = self._edited_targets_only(Relation.COUNTRY)
        if country_associated_with is None:
            country_associated_with = self._edited_targets_only(Relation.CAPITAL_OF)
        new_continent = self._targets_of(country_associated_with, Relation.CURRENCY)
        return TestCase(
            test_query=Query(self.subject_id, Relation.CURRENCY, new_continent),
            condition_queries=self.conditions
        )

    def official_language(self):
        self.empty_conditions()
        country_associated_with = self._edited_targets_only(Relation.COUNTRY)
        if country_associated_with is None:
            country_associated_with = self._edited_targets_only(Relation.CAPITAL_OF)
        new_continent = self._targets_of(country_associated_with, Relation.OFFICIAL_LANGUAGE)
        return TestCase(
            test_query=Query(self.subject_id, Relation.OFFICIAL_LANGUAGE, new_continent),
            condition_queries=self.conditions
        )

    def likely_anthem(self):
        self.empty_conditions()
        country_associated_with = self._edited_targets_only(Relation.COUNTRY)
        if country_associated_with is None:
            country_associated_with = self._edited_targets_only(Relation.CAPITAL_OF)
        new_continent = self._targets_of(country_associated_with, Relation.ANTHEM)
        return TestCase(
            test_query=Query(self.subject_id, Relation.LIKELY_ANTHEM, new_continent),
            condition_queries=self.conditions
        )


def add_test(tests, test):
    if test is None:
        return
    tests.append(test)


def generate_constraints(subject_id: str, relation: Relation, new_target_id: str):
    tests = []
    constraints = RelationalConstraints(subject_id, {relation: [new_target_id]})

    if relation == Relation.MOTHER:
        add_test(tests, constraints.sibling())
        add_test(tests, constraints.uncle())
        add_test(tests, constraints.aunt())
        add_test(tests, constraints.mothers_child())
        add_test(tests, constraints.mothers_number_of_children())

    if relation == Relation.FATHER:
        add_test(tests, constraints.sibling())
        add_test(tests, constraints.uncle())
        add_test(tests, constraints.aunt())
        add_test(tests, constraints.fathers_child())
        add_test(tests, constraints.fathers_number_of_children())

    if relation == Relation.BROTHER:
        add_test(tests, constraints.mother_or_father_child())
        add_test(tests, constraints.mother_or_father_of_new_sibling())
        add_test(tests, constraints.sibling_of_new_sibling())

    if relation == Relation.SISTER:
        add_test(tests, constraints.mother_or_father_child())
        add_test(tests, constraints.mother_or_father_of_new_sibling())
        add_test(tests, constraints.sibling_of_new_sibling())

    if relation == Relation.SIBLING:
        add_test(tests, constraints.mother_or_father_child())
        add_test(tests, constraints.mother_or_father_of_new_sibling())
        add_test(tests, constraints.sibling_of_new_sibling())

    if relation == Relation.SPOUSE:
        add_test(tests, constraints.spouse_of_new_spouse())

    if relation == Relation.PLACE_OF_DEATH:
        add_test(tests, constraints.is_dead_now())

    if relation == Relation.PLACE_OF_BURIAL:
        add_test(tests, constraints.is_dead_now())

    if relation == Relation.DATE_OF_DEATH:
        add_test(tests, constraints.is_dead_now())

    if relation == Relation.FOLLOWS:
        add_test(tests, constraints.new_followed_by())

    if relation == Relation.FOLLOWED_BY:
        add_test(tests, constraints.new_follows())

    if relation == Relation.COUNTRY:
        add_test(tests, constraints.continent())
        add_test(tests, constraints.currency())
        add_test(tests, constraints.official_language())
        add_test(tests, constraints.likely_anthem())

    if relation == Relation.CAPITAL_OF:
        add_test(tests, constraints.continent())
        add_test(tests, constraints.currency())
        add_test(tests, constraints.official_language())
        add_test(tests, constraints.likely_anthem())

    return tests



