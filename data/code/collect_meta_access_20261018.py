"""Capture public Meta access attempts, including blocked responses.

No credentials or login bypass. HTTP 200 alone does not establish post coverage.
Run once; raw responses and manifest remain separate from social metrics.
"""
from pathlib import Path
import csv
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data/raw/online_20261018'

def main():
    if (BASE / 'meta_access_manifest.json').exists():
        raise FileExistsError('Snapshot already exists; use a new dated destination to preserve raw responses.')
    sources = [
        ('Meta Content Library', 'https://transparency.meta.com/researchtools/meta-content-library/'),
        ('Meta research announcement', 'https://about.fb.com/news/2023/11/new-tools-to-support-independent-research/'),
        ('SOMAR', 'https://www.icpsr.umich.edu/sites/somar/meta-content-library'),
        ('Ad Library API', 'https://www.facebook.com/ads/library/api/'),
    ]
    with (ROOT / 'data/processed/candidate_campaign_sources.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['source_kind'] == 'facebook.com':
                sources.append((r['candidate_name'], r['url']))
    attempts = []
    for i, (name, url) in enumerate(dict.fromkeys(sources), 1):
        path = BASE / f'meta_access_{i:02d}.html'
        result = subprocess.run(['curl', '-L', '--silent', '--show-error', '--max-time', '20',
                                 '-w', '%{http_code}', url, '-o', str(path)], capture_output=True, text=True)
        record = dict(subject=name, url=url, captured_date='2026-10-18', http_status=result.stdout,
                      return_code=result.returncode, error=result.stderr.strip(),
                      interpretation='response_only_not_verified_posts', posts_collected=None,
                      complete_window=False)
        if path.exists():
            record.update(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        attempts.append(record)
    (BASE / 'meta_access_manifest.json').write_text(json.dumps(attempts, ensure_ascii=False, indent=2))
    print([(x['subject'], x['http_status']) for x in attempts])

if __name__ == '__main__':
    main()
