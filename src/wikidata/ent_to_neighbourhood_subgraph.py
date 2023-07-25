import json
import os
from collections import defaultdict
from wikidata.utils import retrieve_from_wikidata


def depth_k_neighbourhood(ent: str, depth: int, wikidata_dir):
    subgraph = dict()
    layer_end = 'layer end'
    queue = [ent, layer_end]
    curr_level = 1
    while queue and curr_level <= depth:
        curr_ent = queue.pop(0)
        if curr_ent == layer_end:
            curr_level += 1
            continue
        curr_facts = retrieve_from_wikidata(curr_ent, wikidata_dir)
        if not curr_facts:
            queue.append(layer_end)
            continue
        relation2targets_dict = defaultdict(list)
        for relation, target in curr_facts:
            relation2targets_dict[relation].append(target)
            queue.append(target)
        subgraph[curr_ent] = relation2targets_dict
        queue.append(layer_end)
    
    return subgraph
