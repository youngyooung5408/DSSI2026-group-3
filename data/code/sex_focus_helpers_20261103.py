"""Read-only extraction helpers for the 2026 council sex-evidence review."""
import csv
import json
import re
import unicodedata
from collections import defaultdict
from bs4 import BeautifulSoup

WIKI_TITLE = '2026年中華民國直轄市議員及縣市議員選舉選舉區投票結果列表'
WIKI_URL = 'https://zh.wikipedia.org/zh-tw/' + WIKI_TITLE
RAW = 'data/raw/sex_focus_20261103/'


def norm(value):
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC', value)).casefold().replace('台', '臺').replace('温', '溫')


def chinese_name(value):
    return ''.join(re.findall(r'[\u3400-\u9fff]', norm(value)))


def district_number(value):
    hit = re.search(r'第([一二三四五六七八九十零〇兩\d]+)選舉區', value)
    if not hit:
        return ''
    value = hit[1]
    if value.isdigit():
        return str(int(value))
    digits = dict(zip('零一二三四五六七八九', range(10)))
    digits.update({'〇': 0, '兩': 2})
    if '十' in value:
        left, right = value.split('十')
        return str(digits.get(left, 1) * 10 + digits.get(right, 0))
    return str(digits[value])


def read_csv(root, path):
    with (root / path).open(encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def body(root, path):
    soup = BeautifulSoup((root / path).read_bytes(), 'html.parser')
    for item in soup(['script', 'style', 'nav', 'footer', 'header']):
        item.decompose()
    return soup.get_text(' ', strip=True)


def extract_wiki(root, path, url, version):
    raw = (root / path).read_bytes()
    if path.endswith('.json'):
        raw = json.loads(raw)['parse']['text']['*']
    soup = BeautifulSoup(raw, 'html.parser')
    county = district = anchor = ''
    result = []
    table_number = 0
    for tag in soup.find_all(['h3', 'h4', 'table']):
        if tag.name == 'h3':
            county = re.sub(r'\[.*?\]', '', tag.get_text(' ', strip=True)).strip()
        elif tag.name == 'h4':
            district = re.sub(r'\[.*?\]', '', tag.get_text(' ', strip=True)).strip()
            id_tag = tag.find(id=True)
            anchor = tag.get('id') or (id_tag.get('id') if id_tag else '')
        elif '性別' in tag.get_text()[:300]:
            table_number += 1
            header = [c.get_text(' ', strip=True) for c in tag.find('tr').find_all(['td', 'th'], recursive=False)]
            assert header[:4] == ['號次', '候選人', '性別', '政黨'], header
            for row_number, tr in enumerate(tag.find_all('tr')[1:], 2):
                values = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)]
                if len(values) >= 4 and values[2] in {'男', '女'}:
                    assert district_number(district), district
                    result.append(dict(county_city=county, district_number=district_number(district),
                        electoral_district_source=district, ballot_number=values[0], source_name=values[1],
                        sex=values[2], party_source=values[3], source_url=url + ('#' + anchor if anchor else ''),
                        source_file=path, source_locator=f'table {table_number}; row {row_number}',
                        source_version=version, row_text=' | '.join(values[:4])))
    return result


def index_wiki(rows):
    result = defaultdict(list)
    for row in rows:
        result[(norm(row['county_city']), row['district_number'], chinese_name(row['source_name']))].append(row)
    return result


def match_wiki(registration, index, source_name=None):
    name = source_name or registration['candidate_name']
    key = (norm(registration['county_city']), district_number(registration['electoral_district']), chinese_name(name))
    hits = index[key]
    if len(hits) == 1:
        return hits[0]
    assert len(hits) == 0, ('ambiguous source match', key, hits)
    return None


def historical_council_index(root):
    """Use official county codes and explicit sex codes, retaining exact row locations."""
    geo = {}
    inputs = []
    for kind in ('T1_city', 'T1_prv', 'T2_city', 'T2_prv', 'T3_city', 'T3_prv'):
        path = f'data/raw/council_review_20261019/{kind}_elbase.csv'
        inputs.append(path)
        with (root / path).open(encoding='utf-8-sig') as stream:
            for row in csv.reader(stream):
                if len(row) > 5 and row[2:5] == ['00', '000', '0000']:
                    key = tuple(row[:2])
                    assert key not in geo or geo[key] == row[5]
                    geo[key] = row[5]
    index = defaultdict(list)
    for i in range(106, 112):
        path = f'data/raw/cec_all_offices/{i:03d}_elcand.csv'
        inputs.append(path)
        with (root / path).open(encoding='utf-8-sig') as stream:
            for line, row in enumerate(csv.reader(stream), 1):
                assert len(row) == 16
                county = geo[tuple(row[:2])]
                record = dict(source_name=row[6], county_city=county, district_number=str(int(row[2])),
                    sex={'1': '男', '2': '女'}[row[8]], source_file=path, source_row=str(line),
                    source_year='2022', birth_roc=row[9])
                index[(norm(county), str(int(row[2])), chinese_name(row[6]))].append(record)
    return index, inputs
