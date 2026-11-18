"""Download 2026 (民國115年) CEC election bulletins (選舉公報) for the 280-candidate scope.

Scope: every county/city head (縣市長) bulletin in all 22 counties, plus the
Taipei and Kaohsiung city-council (市議員) bulletins.

Source: https://eebulletin.cec.gov.tw/ directory listing (?dir=115/...). PDFs are
saved unchanged under data/raw/cec_bulletin_2026/<county>/<office folder>/ with a
manifest recording source URL, retrieval time, bytes and SHA-256. Reruns skip
files already saved.

    python data/code/collect_bulletin_2026.py
"""
from pathlib import Path
import datetime, hashlib, json, re, time, urllib.error, urllib.parse, urllib.request

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]
            if (p / 'AGENTS.md').is_file() and (p / 'templates').is_dir())
BASE = 'https://eebulletin.cec.gov.tw/'
RAW = ROOT / 'data/raw/cec_bulletin_2026'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/130.0 Safari/537.36')
COUNCIL_COUNTIES = ('臺北市', '高雄市')


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def listing(d):
    html = get(BASE + '?dir=' + urllib.parse.quote(d, safe='')).decode('utf-8', 'replace')
    subdirs = sorted({urllib.parse.unquote(m) for m in re.findall(r'href="\?dir=([^"]+)"', html)})
    pdfs = sorted({urllib.parse.unquote(m) for m in re.findall(r'href="([^"?#]+\.pdf)"', html)})
    return [s for s in subdirs if s.startswith(d + '/')], pdfs


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    man_path = RAW / 'file_manifest.json'
    manifest = json.loads(man_path.read_text(encoding='utf-8')) if man_path.exists() else []
    saved = {m['source_path'] for m in manifest}
    failures = []
    counties, _ = listing('115')
    assert len(counties) == 22, counties
    for cdir in counties:
        county = re.sub(r'^\d+', '', cdir.split('/')[-1])
        time.sleep(1)
        offices, _ = listing(cdir)
        wanted = [o for o in offices if re.search(r'/01(市長|縣長)$', o)]
        if county in COUNCIL_COUNTIES:
            wanted += [o for o in offices if re.search(r'/02市議員$', o)]
        assert any(re.search(r'/01(市長|縣長)$', o) for o in wanted), (cdir, offices)
        for odir in wanted:
            time.sleep(1)
            _, pdfs = listing(odir)
            for src in pdfs:
                if src in saved:
                    continue
                time.sleep(1)
                try:
                    body = get(BASE + urllib.parse.quote(src))
                except urllib.error.HTTPError as e:
                    # Some listed links are broken on the CEC site itself; record, do not hide.
                    failures.append(dict(source_path=src, source_url=BASE + urllib.parse.quote(src), status=e.code,
                                         checked_at=datetime.datetime.now().astimezone().isoformat()))
                    (RAW / 'download_failures.json').write_text(json.dumps(failures, ensure_ascii=False, indent=1),
                                                                encoding='utf-8')
                    print('failed', src, e.code, flush=True)
                    continue
                assert body[:5] == b'%PDF-', src
                rel = Path('data/raw/cec_bulletin_2026') / Path(*Path(src).parts[1:])
                (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
                (ROOT / rel).write_bytes(body)
                manifest.append(dict(path=rel.as_posix(), source_path=src, source_url=BASE + urllib.parse.quote(src),
                                     county_city=county, office_folder=odir.split('/')[-1],
                                     retrieved_at=datetime.datetime.now().astimezone().isoformat(),
                                     bytes=len(body), sha256=hashlib.sha256(body).hexdigest()))
                saved.add(src)
                man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
                print('saved', rel.as_posix(), len(body), flush=True)
    print('files', len(manifest))


if __name__ == '__main__':
    main()
