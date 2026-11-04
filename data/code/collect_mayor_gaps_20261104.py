"""Download public pages for the 2026 mayoral G1/G2/G3/G5 gap review.

Usage: py -3 data/code/collect_mayor_gaps_20261104.py
Reads data/code/mayor_gaps_sources_20261104.json ({"label": url}), saves each
response under data/raw/mayor_gaps_20261104/ and appends to manifest.json.
Already-downloaded labels are skipped so earlier captures stay unchanged.
Failed downloads are recorded with their error, never as successful captures.
`sha256` hashes the exact downloaded bytes; `sha256_lf` hashes them after CRLF->LF,
which stays stable when Git converts line endings on checkout.
"""
from pathlib import Path
import datetime, hashlib, json, urllib.parse, urllib.request

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'AGENTS.md').exists() and (p / 'templates').exists())
SOURCES = ROOT / 'data/code/mayor_gaps_sources_20261104.json'
RAW = ROOT / 'data/raw/mayor_gaps_20261104'
MANIFEST = RAW / 'manifest.json'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
CRLF, LF = b'\r\n', b'\n'


def iri_to_uri(url):
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(parts.path, safe='/%:')
    query = urllib.parse.quote(parts.query, safe='=&%')
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, query, ''))


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    sources = json.loads(SOURCES.read_text(encoding='utf-8'))
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else []
    done = {m['label'] for m in manifest if m['status'] == 'ok'}
    for label, url in sources.items():
        if label in done:
            continue
        entry = dict(label=label, url=url, fetched_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'))
        try:
            req = urllib.request.Request(iri_to_uri(url), headers={'User-Agent': UA, 'Accept-Language': 'zh-TW,zh;q=0.9'})
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read()
                entry.update(http_status=r.status, final_url=r.geturl())
            path = RAW / f'{label}.html'
            path.write_bytes(body)
            entry.update(status='ok', file=path.relative_to(ROOT).as_posix(), bytes=len(body),
                         sha256=hashlib.sha256(body).hexdigest(),
                         sha256_lf=hashlib.sha256(body.replace(CRLF, LF)).hexdigest())
        except Exception as e:  # keep the failure, do not treat it as a capture
            entry.update(status='failed', error=f'{type(e).__name__}: {e}')
        manifest = [m for m in manifest if m['label'] != label] + [entry]
        print(entry['status'], label, entry.get('bytes', entry.get('error')))
    with MANIFEST.open('w', encoding='utf-8', newline='') as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
