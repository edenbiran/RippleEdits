from build_benchmark import construct_recently_modified_benchmark
from wikidata.utils import load_json, ent_label2id
import matplotlib.pyplot as plt


recently_modified_facts = construct_recently_modified_benchmark()

# number of facts / popularities
collection = []
for example in recently_modified_facts:
    ent2num_of_facts = load_json('./subject2num_of_facts.json')
    subject_id = example.fact._subject_id
    collection.append(ent2num_of_facts[ent_label2id(subject_id)])
print(len(collection))
