import random
from wikidata.utils import load_json, write_json


if __name__ == '__main__':
    relation2optional_targets = load_json('./wikidata/relation2optional_targets.json')
    sampled_facts = load_json('./wikidata/100_sampled_facts.json')
    dataset = []
    for fact in sampled_facts:
        subject, relation_target = fact
        relation, target = relation_target
        optional_targets = relation2optional_targets[relation]
        random_target = random.sample(optional_targets, 1)[0]
        counterfactual = (subject, relation, random_target)
        dataset.append({'fact': (subject, relation, target), 'counterfactual': counterfactual})

        print(fact)
        print(counterfactual)
        print('\n')

    write_json(dataset, './generations/fact_and_counterfactual_samples1.json')