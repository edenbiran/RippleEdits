import itertools
import requests
import json

from relation import Relation


def query(request):
    request['action'] = 'query'
    request['format'] = 'json'
    last_continue = {}
    while True:
        # Clone original request
        req = request.copy()
        # Modify it with the values returned in the 'continue' section of the last result.
        req.update(last_continue)
        # Call API
        result = requests.get('https://en.wikipedia.org/w/api.php', params=req).json()
        if 'error' in result:
            raise Exception(result['error'])
        if 'warnings' in result:
            print(result['warnings'])
        if 'query' in result:
            yield result['query']
        if 'continue' not in result:
            break
        last_continue = result['continue']


def get_wikidata_id_by_title(title):
    req = {'format': 'json', 'action': 'query', 'prop': 'pageprops', 'titles': title}
    result = requests.get('https://en.wikipedia.org/w/api.php', params=req).json()
    return list(result['query']['pages'].values())[0]['pageprops']['wikibase_item']


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(itertools.islice(it, size)), ())


def get_top_pages_by_date(year, month, day):
    month = str(month).rjust(2, '0')
    if day == 0:
        day = 'all-days'
    else:
        day = str(day).rjust(2, '0')
    url = f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia.org/all-access/{year}/{month}/{day}'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36'}
    pageview_results = requests.get(url, headers=headers).json()

    article_names = [page_info['article'] for page_info in pageview_results['items'][0]['articles']]
    wikidata_ids = dict()
    for batch in chunk(article_names, 50):
        pageprops_result = requests.get('https://en.wikipedia.org/w/api.php', params={'format': 'json', 'action': 'query', 'prop': 'pageprops', 'titles': '|'.join(batch)}).json()
        pages = pageprops_result['query']['pages']
        for info in pages.values():
            try:
                wikidata_ids[info['title']] = info['pageprops']['wikibase_item']
            except KeyError:
                # print(f'Failed getting info for {info}')
                pass

    wikidata_claims = dict()
    wanted_relations = set([relation.id() for relation in Relation])
    for batch in chunk(wikidata_ids.values(), 50):
        claims_result = requests.get('https://wikidata.org/w/api.php', params={'format': 'json', 'action': 'wbgetentities', 'prop': 'claims', 'languages': 'en', 'ids': '|'.join(batch)}).json()
        for entity_id, entity_info in claims_result['entities'].items():
            claims = list(entity_info['claims'].keys())
            if any(x in wanted_relations for x in claims):
                wikidata_claims[entity_id] = claims

    top_pages = []
    articles = pageview_results['items'][0]['articles']
    for page_info in articles:
        try:
            page = dict()
            page['title'] = page_info['article'].replace('_', ' ')
            page['id'] = wikidata_ids[page['title']]
            page['views'] = page_info['views']
            if page['id'] in wikidata_claims:
                top_pages.append(page)
        except KeyError:
            # print(f'Failed getting info for {page_info}')
            pass

    return top_pages


def generate_monthly():
    results = dict()

    for year in ['2020', '2021', '2022']:
        for month in range(1, 13):
            month = str(month).rjust(2, '0')
            results[year + month] = get_top_pages_by_date(year, month, 0)
            print(f'Completed: {month}/{year}')
            with open('top_entities_by_views_monthly.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    for month in range(1, 5):
        month = str(month).rjust(2, '0')
        results['2023' + month] = get_top_pages_by_date(2023, month, 0)
        print(f'Completed: {month}/2023')
        with open('top_entities_by_views_monthly.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    generate_monthly()
