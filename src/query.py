from relation import Relation
from wikidata.utils import get_label, get_aliases


class Query:

    def __init__(self, subject_id, relation, target_ids, phrase=None):
        self._subject_id = subject_id
        self._relation = relation
        self._targets_ids = target_ids if type(target_ids) == list else [target_ids]
        self._phrase = phrase

    def get_query_prompt(self):
        if self._phrase is None:
            return self._relation.phrase(get_label(self._subject_id))
        return self._phrase

    @staticmethod
    def _filter_answers(answers):
        filtered_answers = []
        for answer in answers:
            if len(answer) > 1 or answer.isdigit():
                filtered_answers.append(answer)
        return filtered_answers

    def get_answers(self):
        answers = []
        for target in self._targets_ids:
            if type(target) is str:
                target_answer = [get_label(target)] + get_aliases(target)
            else:
                target_answer = [str(target)]
            answers.append(self._filter_answers(target_answer))
        return answers

    def to_dict(self):
        return {
            'prompt': self.get_query_prompt(),
            'answers': [{'value': get_label(target), 'aliases': get_aliases(target)} if type(target) == str and target[0] == 'Q'
                        else {'value': str(target), 'aliases': []} for target in self._targets_ids],
            'query_type': 'regular',
            'subject_id': self._subject_id,
            'relation': self._relation.name,
            'target_ids': self._targets_ids,
            'phrase': self._phrase,
        }

    @staticmethod
    def from_dict(d):
        subject_id = d['subject_id']
        relation = Relation[d['relation']]
        target_ids = d['target_ids']
        phrase = d['phrase']
        if d['query_type'] == 'regular':
            return Query(subject_id, relation, target_ids, phrase)
        elif d['query_type'] == 'two_hop':
            second_relation = Relation[d['second_relation']]
            second_hop_target_ids = d['second_hop_target_ids']
            return TwoHopQuery(subject_id, relation, target_ids, second_relation, second_hop_target_ids, phrase)
        else:
            print('Unknown phrase type: ', d['query_type'])


class TwoHopQuery(Query):

    def __init__(self, subject_id, relation, target_ids, second_relation, second_hop_target_ids, phrase):
        super().__init__(subject_id, relation, target_ids, phrase)
        self._second_relation = second_relation
        self._second_hop_target_ids = second_hop_target_ids if type(second_hop_target_ids) == list else [second_hop_target_ids]

    def get_query_prompt(self):
        return self._phrase

    def get_answers(self):
        answers = []
        for target in self._second_hop_target_ids:
            if type(target) is str:
                target_answer = [get_label(target)] + get_aliases(target)
            else:
                target_answer = [str(target)]
            answers.append(self._filter_answers(target_answer))
        return answers

    def to_dict(self):
        d = super().to_dict()
        d['query_type'] = 'two_hop'
        d['second_relation'] = self._second_relation.name
        d['second_hop_target_ids'] = self._second_hop_target_ids
        d['answers'] = [{'value': get_label(target), 'aliases': get_aliases(target)}
                        if type(target) == str and len(target) >= 2 and target[0] == 'Q' and target[1].isdigit()
                        else {'value': str(target), 'aliases': []} for target in self._second_hop_target_ids]
        return d
