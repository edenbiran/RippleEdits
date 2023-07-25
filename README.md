# Evaluating the Ripple Effects of Knowledge Editing in Language Models

This repository contains the official code of the paper: ["Evaluating the Ripple Effects of Knowledge Editing in Language Models"](https://arxiv.org/abs/2307.12976).

## Setup

The benchmark creation and all experiments and evaluations were conducted in a Python 3.9 environment.
To clone the repository and set up the environment, please run the following commands:
```shell
git clone https://github.com/edenbiran/RippleEdits.git
cd RippleEdits
pip install -r requirements.txt
```

## RippleEdits Benchmark

The benchmark files and statistics can be found under `data/benchmark/` and `data/stats/`. 
The benchmark is split into three files named according to the benchmark\`s three subsets: `RECENT`, `RANDOM` and `POPULAR`. 
For more details please refer to section 4 of the paper.

The source code for generating the benchmark can be found under `src/`.

Generating the benchmark from scratch can be done using `src/build_benchmark.py`.
Benchmark popularity statistics can be extracted using `src/benchmark_statistics.py`.

Each benchmark json contains a list of entries. 
Each entry is an edit containing the edit information (which also contains the original fact if applicable) and the 6 evaluation criteria.
Each evaluation criteria contains a list of tests, where each test contains the test prompt, answers and conditions.
An example (shortened for brevity) of an edit entry can be seen below:
```json
{
  "example_type": "popular",
  "edit": {
    "prompt": "The name of the country of citizenship of Leonardo DiCaprio is Syria.",
    "subject_id": "Q38111",
    "relation": "COUNTRY_OF_CITIZENSHIP",
    "target_id": "Q858",
    "original_fact": {
      "prompt": "The name of the country of citizenship of Leonardo DiCaprio is United States of America.",
      "subject_id": "Q38111",
      "relation": "COUNTRY_OF_CITIZENSHIP",
      "target_id": "Q30"
    }
  },
  "Relation_Specifity": [
    {
      "test_queries": [
        {
          "prompt": "The name of the mother of Leonardo DiCaprio is",
          "answers": [
            {
              "value": "Irmelin DiCaprio",
              "aliases": [
                "Irmelin Indenbirken",
                "Irmelin Indenbirken-DiCaprio"
              ]
            }
          ],
          "query_type": "regular",
          "subject_id": "Q38111",
          "relation": "MOTHER",
          "target_ids": [
            "Q22984557"
          ],
          "phrase": null
        }
      ],
      "test_condition": "OR",
      "condition_queries": [
        {
          "prompt": "The name of the mother of Leonardo DiCaprio is",
          "answers": [
            {
              "value": "Irmelin DiCaprio",
              "aliases": [
                "Irmelin Indenbirken",
                "Irmelin Indenbirken-DiCaprio"
              ]
            }
          ],
          "query_type": "regular",
          "subject_id": "Q38111",
          "relation": "MOTHER",
          "target_ids": [
            "Q22984557"
          ],
          "phrase": null
        }
      ]
    },
  ...
  ],
  "Logical_Generalization": [...],
  "Subject_Aliasing": [...],
  "Compositionality_I": [...],
  "Compositionality_II": [...],
  "Forgetfulness": [...]
}
```

## Evaluation

The source code for all evaluations of the benchmark can be found under `src/`. 
All evaluations can be conducted using `src/evaluation.py`.

In order to evaluate the benchmark on a language model not currently supported extend the class `QueryExecutor` in `src/queryexecutor.py` and add the new `QueryExecutor` to `src/evaluation.py`.

In order to evaluate the benchmark on a knowledge editing technique not currently supported extend the class `ModelEditor` in `src/modeleditor.py` and add the new `ModelEditor` to `src/evaluation.py`.

## Citation
```
@misc{cohen2023evaluating,
      title={Evaluating the Ripple Effects of Knowledge Editing in Language Models}, 
      author={Roi Cohen and Eden Biran and Ori Yoran and Amir Globerson and Mor Geva},
      year={2023},
      eprint={2307.12976},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```