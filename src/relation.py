from enum import Enum
from wikidata.utils import subject_relation_to_targets
from utils import compute_exact_match


class Relation(Enum):

    # Subject is a person
    MOTHER = ('P25', 'The name of the mother of <subject> is', ['BROTHER', 'SISTER', 'SIBLING', 'UNCLE', 'AUNT'], True)
    FATHER = ('P22', 'The name of the father of <subject> is', ['BROTHER', 'SISTER', 'SIBLING', 'UNCLE', 'AUNT'], True)
    BROTHER = ('P7', 'The name of the brother of <subject> is', ['SIBLING'], False)
    SISTER = ('P9', 'The name of the sister of <subject> is', ['SIBLING'], False)
    SIBLING = ('P3373', "The names of the siblings of <subject> are", ['BROTHER', 'SISTER'], False)
    SPOUSE = ('P26', "The name of the spouse of <subject> is", [], False)
    UNCLE = ('', 'The name of the uncle of <subject> is', [], False)
    AUNT = ('', 'The name of the aunt of <subject> is', [], False)
    CHILD = ('P40', 'The name of the child of <subject> is', ['NUMBER_OF_CHILDREN'], False)
    NUMBER_OF_CHILDREN = ('P1971', 'The number of children <subject> has is', [], True)
    SEX_OR_GENDER = ('P21', "The gender of <subject> is", [], True)
    PLACE_OF_BIRTH = ('P19', 'The place of birth of <subject> is', [], True)
    PLACE_OF_DEATH = ('P20', 'The place of death of <subject> is', ['is alive'], True)
    PLACE_OF_BURIAL = ('P119', 'The place of burial of <subject> is', ['is alive'], True)
    COUNTRY = ('P17', 'The name of the country which <subject> is associated with is',
               ['continent', 'official language', 'capital of', 'currency'], True)
    COUNTRY_OF_CITIZENSHIP = ('P27', 'The name of the country of citizenship of <subject> is', [], False)
    POSITION_HELD = ('P39', 'The name of the position held by <subject> is', [], False)
    STEPFATHER = ('P43', 'The name of the stepfather of <subject> is', ['number of children'], True)
    STEPMOTHER = ('P44', 'The name of the stepmother of <subject> is', [], True)
    MEMBER_OF_SPORTS_TEAM = ('P54', 'The name of the sports team which <subject> is a member of is', [], False)
    ALMA_MATER = ('P69', 'The name of the alma mater of <subject> is', [], False)
    SEXUAL_ORIENTATION = ('P91', "The sexual orientation of <subject> is", [], False)
    OCCUPATION = ('P106', 'The occupation of <subject> is', ['field of work'], False)
    EMPLOYER = ('P108', "The name of the employer of <subject> is", [], False)
    LEAGUE = ('P118', 'The name of the league which <subject> plays in is', [], False)
    FIELD_OF_WORK = ('P101', 'The name of the field of work of <subject> is', ['occupation'], False)
    NATIVE_LANGUAGE = ('P03', 'The mother tongue of <subject> is', [], False)
    AWARD_RECEIVED = ('P166', 'The name of the award <subject> won is', [], False)
    FOLLOWS = ('P155', '<subject> follows', [], True)
    FOLLOWED_BY = ('P156', '<subject> is followed by', [], True)
    ETHNIC_GROUP = ('P172', 'The name of the ethnic group which <subject> is associated with is', ['religion'], False)
    RELIGION = ('P140', 'The name of the religion which <subject> is associated with is', [], False)
    EYE_COLOR = ('P1340', 'The eye color of <subject> is', [], True)
    DATE_OF_BIRTH = ('P569', 'The date of birth of <subject> is', [], True)
    DATE_OF_DEATH = ('P570', 'The date of death of <subject> is', ['is alive'], True)
    IS_ALIVE = ('', 'Is <subject> still alive?', ['place of death', 'place of burial', 'date of death'], True)

    # Subject is a country
    HEAD_OF_GOVERNMENT = ('P6', 'The name of the head of government of <subject> is', ['head of state'], False)
    HEAD_OF_STATE = ('P35', 'The name of the head of state of <subject> is', ['head of government'], False)
    CONTINENT = ('P30', 'The name of the continent which <subject> is part of is', ['country'], True)
    CAPITAL = ('P36', 'The name of the capital city of <subject> is', [], True)
    CURRENCY = ('P38', 'The name of the currency in <subject> is', [], False)
    OFFICIAL_LANGUAGE = ('P37', 'The official language of <subject> is', [], False)
    ANTHEM = ('P85', 'The name of the anthem of <subject> is', [], True)
    LIKELY_ANTHEM = ('', 'The name of the anthem that is most likely to be performed in <subject> is', [], True)

    # Subject is a city
    CAPITAL_OF = ('P1376', 'The name of the country which <subject> is the capital of is',
                  ['country', 'continent', 'currency', 'official language', 'anthem'], True)

    # Subject is a book
    AUTHOR = ('P50', 'The name of the author of <subject> is', [], False)
    EDITOR = ('P98', 'The name of the editor of <subject> is', [], False)

    # Subject is a movie
    DIRECTOR = ('P57', 'The name of the director of <subject> is', [], False)
    SCREENWRITER = ('P58', 'The name of the screenwriter of <subject> is', [], False)
    CAST_MEMBER = ('P161', "The names of the cast members of <subject> are", [], False)

    # Subject is a building
    ARCHITECT = ('P84', 'The name of the architect of <subject> is', [], False)

    # Subject is a musical piece
    COMPOSER = ('P86', 'The name of the composer of <subject> is', [], False)

    # Subject is a company
    FOUNDER = ('P112', 'The name of the founder of <subject> is', [], False)

    def __init__(self, relation_id, phrase, impacted_relations, is_modification):
        self._relation_id = relation_id
        self._phrase = phrase
        self._impacted_relations = impacted_relations
        self._is_modification = is_modification

    def id(self):
        return self._relation_id

    def phrase(self, subject):
        if isinstance(subject, list):
            if subject:
                subject = subject[0]
            else:
                return self._phrase
        return self._phrase.replace('<subject>', subject)

    def evaluate(self, subject):
        return subject_relation_to_targets(subject, self._relation_id)

    def impacted_relations(self):
        return [self.string_to_enum(r) for r in self._impacted_relations]

    def is_modification(self):
        return self._is_modification

    def formal_name(self):
        return self.name.lower().replace('_', ' ')

    @staticmethod
    def string_to_enum(relation_name: str):
        processed_relation_name = relation_name.replace(' ', '_')
        for relation in Relation:
            if compute_exact_match(processed_relation_name, relation.name):
                return relation
        return None

    @staticmethod
    def id_to_enum(relation_id: str):
        for relation in Relation:
            if compute_exact_match(relation_id, relation.id()):
                return relation
        return None
