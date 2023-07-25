import argparse
import os
import numpy as np
from matplotlib import pyplot as plt


def main(args):
    scores = []
    file_count = 0
    for filename in os.listdir(args.results_dir):
        file_count += 1
        plot_result = dict(np.load(os.path.join(args.results_dir, filename), allow_pickle=True))
        if not plot_result['correct_prediction'] or plot_result['kind'] != 'mlp':
            continue
        layer_scores = np.sum(plot_result['scores'], axis=0)
        normalized_layer_scores = layer_scores / np.sum(layer_scores)
        scores.append(normalized_layer_scores)

    total_scores = np.sum(scores, axis=0)
    normalized_total_scores = total_scores / np.sum(total_scores)
    print(f'Using {len(scores)} / {file_count // 3} tests the layer with the highest score is layer {np.argmax(normalized_total_scores)}')

    plt.ylabel('Score')
    plt.xlabel('Layer')
    plt.plot(normalized_total_scores)
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Causal Tracing Averages")
    parser.add_argument("results_dir")
    main(parser.parse_args())
