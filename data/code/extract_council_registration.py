"""Convert the two saved CEC PDFs to page/table JSON; requires pdfplumber.

Run before prepare_council_and_meta_20261018.ipynb. Preserve all table cells.
"""
from pathlib import Path
import hashlib
import json
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data/raw/online_20261018'

def extract():
    manifest = json.loads((BASE / 'capture_manifest.json').read_text())
    for stem in ['cec_council_metropolitan', 'cec_council_county']:
        path = BASE / (stem + '.pdf')
        expected = next(x['sha256'] for x in manifest if x['path'] == str(path.relative_to(ROOT)))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        with pdfplumber.open(path) as pdf:
            pages = [{'page': n, 'tables': p.extract_tables()} for n, p in enumerate(pdf.pages, 1)]
        out = BASE / (stem + '_tables.json')
        out.write_text(json.dumps(pages, ensure_ascii=False, indent=2))
        print(out.name, len(pages))

if __name__ == '__main__':
    extract()
