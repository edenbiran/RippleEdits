from wikidata.utils import get_label, get_aliases, write_to_csv
import openai
from openai_key.openai_key import my_openai_key
openai.api_key = my_openai_key


def create_test_example_given_input_targets(input_prompt: str, targets: list):
    test = {
        'input_prompt': input_prompt,
        'answers': [{'value': get_label(target), 'aliases': get_aliases(target)} if type(target) == str
                    else {'value': str(target), 'aliases': []} for target in targets]
    }
    return test


def normalize_text(s):
    """Removing articles and punctuation, and standardizing whitespace are all typical text processing steps."""
    import string, re

    def remove_articles(text):
        regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
        return re.sub(regex, " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def compute_exact_match(prediction, truth):
    return int(normalize_text(prediction) == normalize_text(truth))


def call_openai(prompt, model='text-davinci-003', temperature=0, max_tokens=15):
    response = openai_key.Completion.create(
        model=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        logprobs=5,
        # stop=["\"\"\""],
    )
    top_logprobs = response['choices'][0]['logprobs']['top_logprobs']
    text = response['choices'][0]['text']
    write_to_csv('./gpt3_data/gpt3_calls.csv', [[prompt, text]])
    return text, top_logprobs


def process_generation(text: str):  #diffrence between this and normlize text?? ask roi
    if not text:
        return text
    while text and text[0] in ['\n', ':', ' ', ',', ';']:
        text = text[1:]
    return text
