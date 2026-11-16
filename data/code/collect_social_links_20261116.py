"""Collect public sources for missing candidate social links (2026-11-16 round).

Run from anywhere inside the project:
    python data/code/collect_social_links_20261116.py

Stages (each saves raw responses + log; reruns skip URLs already saved):
  1. 串仔 tshng-a.kunlim.cc candidate pages listed in the Taipei / Kaohsiung sitemaps
     (DPP-supporter directory, not official).
  2. DuckDuckGo HTML search for every (candidate, platform) still `not_located`
     in candidate_social_links_scope_20261114.csv; a broader second query is
     sent only when the first returns no profile whose title contains the name.
  3. Link-hub pages (linktr.ee / portaly / lit.link ...) returned by searches whose
     search title contains the candidate name.

Normal browser User-Agent only; no login, cookies, or crawler impersonation.
Facebook / Instagram / Threads profile pages are not fetched (login walls);
their identity evidence is limited to search-result titles and snippets.
"""
from pathlib import Path
import csv, hashlib, json, re, sys, time, datetime, urllib.parse, urllib.request

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]
            if (p / 'AGENTS.md').is_file() and (p / 'templates').is_dir())
SCOPE = 'data/processed/candidate_social_links_scope_20261114.csv'
SCOPE_SHA = 'ac9dab6e14504395106de57eb9d2861dc029e400a743448ec42e756098d68e89'
ROUND1_OUTPUT_SHA = '7741ff845386514230a97d61f9c1ed9e5d346f45c4e571e90caa5986a1148e8c'
RAW = ROOT / 'data/raw/social_links_20261116'
LOG = RAW / 'request_log.json'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/130.0 Safari/537.36')
PLATFORMS = {'Facebook': 'facebook', 'Instagram': 'instagram', 'Threads': 'threads'}
PROFILE_HOST = {'Facebook': 'facebook.com', 'Instagram': 'instagram.com', 'Threads': 'threads.'}
HUB_HOSTS = ('linktr.ee', 'portaly.cc', 'lit.link', 'beacons.ai', 'linkby.tw', 'bio.link', 'msha.ke')
TSHNG = 'https://tshng-a.kunlim.cc'


def core_name(name):
    return re.sub(r'[^㐀-鿿]', '', name)


def load_log():
    return json.loads(LOG.read_text(encoding='utf-8')) if LOG.exists() else []


def save_log(log):
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding='utf-8')


def fetch(url, log, meta, pause):
    done = {r['url']: r for r in log}
    if url in done and done[url]['status'] == 200:
        return (ROOT / done[url]['path']).read_bytes()
    time.sleep(pause)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'zh-TW,zh;q=0.9'})
    status, body = None, b''
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            status, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read() or b''
    except Exception as e:  # network errors are logged, not hidden
        status = f'error:{type(e).__name__}'
    name = hashlib.sha1(url.encode()).hexdigest()[:20] + '.html'
    path = RAW / name
    if body:
        path.write_bytes(body)
    rec = dict(url=url, status=status, fetched_at=datetime.datetime.now().astimezone().isoformat(),
               path=str(path.relative_to(ROOT)).replace('\\', '/') if body else '',
               sha256=hashlib.sha256(body).hexdigest() if body else '', bytes=len(body), **meta)
    log[:] = [r for r in log if r['url'] != url] + [rec]
    save_log(log)
    return body if status == 200 else None


def ddg_results(html):
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, 'html.parser')
    out = []
    for r in s.select('div.result'):
        a = r.select_one('a.result__a')
        if not a:
            continue
        href = urllib.parse.parse_qs(urllib.parse.urlparse(a['href']).query).get('uddg', [a['href']])[0]
        sn = r.select_one('.result__snippet')
        out.append((href, a.get_text(' ', strip=True), sn.get_text(' ', strip=True) if sn else ''))
    return out


def blocked(html):
    return b'anomaly' in html[:20000] or b'challenge' in html[:5000].lower()


def write_manifest(log):
    manifest = [dict(path=x['path'], sha256=x['sha256']) for x in log if x['path']]
    (RAW / 'file_manifest.json').write_text(json.dumps(sorted(manifest, key=lambda m: m['path']),
                                                      ensure_ascii=False, indent=1), encoding='utf-8')
    print('requests', len(log), 'saved', len(manifest))


def main(stages):
    RAW.mkdir(parents=True, exist_ok=True)
    scope_bytes = (ROOT / SCOPE).read_bytes()
    # Round 1 ran against the committed table (SCOPE_SHA); round 2 targets the cells still
    # unfilled after the first in-place update (ROUND1_OUTPUT_SHA).
    expected = ROUND1_OUTPUT_SHA if 'round2' in stages else SCOPE_SHA
    assert hashlib.sha256(scope_bytes).hexdigest() == expected, 'scope table changed'
    rows = list(csv.DictReader(scope_bytes.decode('utf-8-sig').splitlines()))
    assert len(rows) == 280
    log = load_log()

    if 'tshng' in stages:
        for city in ['taipei', 'kaohsiung']:
            sm = fetch(f'{TSHNG}/sitemap-{city}-0.xml', log, dict(stage='tshng_sitemap', city=city), 1.5)
            for loc in re.findall(rb'<loc>([^<]+)</loc>', sm or b''):
                fetch(loc.decode(), log, dict(stage='tshng_page', city=city), 1.5)

    if 'search' in stages:
        # Round-1 design (first 38 candidates, kept as collected): per platform, a contextual
        # query then a plain `{name} {platform}` query if no profile hit.
        # Round-1b design (remaining candidates, faster): one combined query for all three
        # platforms, then a contextual per-platform query only for platforms still without a
        # profile hit. The plain fallback is dropped: for local candidates it mostly returned
        # same-name strangers.
        state = {'fails': 0}
        searched = {x['candidate_key'] for x in log if x.get('stage') == 'ddg_search' and x['status'] == 200}

        def search(q, r, platform, rank):
            url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(q)
            meta = dict(stage='ddg_search', candidate_key=r['candidate_key'], candidate_name=r['candidate_name'],
                        platform=platform, query=q, query_rank=rank)
            for attempt in range(2):
                html = fetch(url, log, meta, 3.5)
                if html is not None and not blocked(html) and b'result__a' in html:
                    state['fails'] = 0
                    return html
                for x in log:  # keep the failed response but mark it for refetch
                    if x['url'] == url and html is not None:
                        x['status'] = 'blocked'
                save_log(log)
                time.sleep(90)
            state['fails'] += 1
            print('blocked/failed', q, file=sys.stderr)
            return None

        for r in rows:
            core = core_name(r['candidate_name'])
            missing = [p for p in PLATFORMS if r[f'{p}_status'] == 'not_located']
            if not missing or r['candidate_key'] in searched:
                continue
            office = '議員' if '議員' in r['office_type'] else ('市長' if '市' in r['county_city'] else '縣長')
            ctx = f'{core} {r["county_city"]}{office}'
            results = []
            html = search(f'{ctx} facebook instagram threads', r, 'all', 1)
            if html:
                results += ddg_results(html)
            # 'quick' stage flag: combined query only (DuckDuckGo rate-limits faster pacing).
            for platform in ([] if 'quick' in stages else missing):
                if any(PROFILE_HOST[platform] in h and core in t for h, t, _ in results):
                    continue
                html = search(f'{ctx} {PLATFORMS[platform]}', r, platform, 2)
                if html:
                    results += ddg_results(html)
            if state['fails'] >= 3:
                print('stopping: repeated search failures', file=sys.stderr)
                write_manifest(log)
                return
            print('done', r['candidate_key'], r['candidate_name'], flush=True)

    if 'round2' in stages:
        # Per-platform contextual query for every cell still unfilled after round 1.
        fails = 0
        for r in rows:
            core = core_name(r['candidate_name'])
            office = '議員' if '議員' in r['office_type'] else ('市長' if '市' in r['county_city'] else '縣長')
            for platform, kw in PLATFORMS.items():
                if r[f'{platform}_status'] not in ('not_located', 'uncertain_same_name_multiple'):
                    continue
                q = f'{core} {r["county_city"]}{office} {kw}'
                url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(q)
                meta = dict(stage='ddg_search', candidate_key=r['candidate_key'], candidate_name=r['candidate_name'],
                            platform=platform, query=q, query_rank=3)
                html = fetch(url, log, meta, 3.5)
                if html is None or blocked(html) or b'result__a' not in html:
                    for x in log:
                        if x['url'] == url and x['status'] == 200:
                            x['status'] = 'blocked'
                    save_log(log)
                    fails += 1
                    print('blocked/failed', q, file=sys.stderr, flush=True)
                    if fails >= 6:
                        print('stopping: repeated search failures', file=sys.stderr)
                        write_manifest(log)
                        return
                    time.sleep(60)
                else:
                    fails = 0
            print('done', r['candidate_key'], flush=True)

    if 'hubs' in stages:
        for rec in [x for x in log if x.get('stage') == 'ddg_search' and x['status'] == 200]:
            core = core_name(rec['candidate_name'])
            for h, t, _ in ddg_results((ROOT / rec['path']).read_bytes()):
                host = urllib.parse.urlparse(h).netloc.lower()
                if any(host.endswith(x) for x in HUB_HOSTS) and core in t:
                    fetch(h, log, dict(stage='link_hub', candidate_key=rec['candidate_key'],
                                       candidate_name=rec['candidate_name'], found_by=rec['url']), 2.0)

    write_manifest(log)


if __name__ == '__main__':
    main(sys.argv[1:] or ['tshng', 'search', 'hubs'])
