"""Extract CEC registration tables unchanged except joining wrapped name lines.

Run from any directory with Python and pdfplumber installed. Original PDFs stay
unchanged. This creates a faithful source-table conversion, not analysis data.
"""
from pathlib import Path
import csv
import hashlib
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    ('2026_metropolitan_registration.pdf', 'C1', 'https://web.cec.gov.tw/api/file/bb9a8d7a-9b8a-41ec-8e23-33efd009385a.pdf', '5ab6ec29145feab84f8e697495f039217bb18ace252382e7e150bb1ea7ae18fa'),
    ('2026_county_registration.pdf', 'C2', 'https://web.cec.gov.tw/api/file/370f3bbf-6408-4fdc-b8d8-9b9214913f74.pdf', '97c32aa206bfd5d1e07d5b9658f853b6b038053b662dd04fdd0132af614a8136'),
]

def extract():
    rows = []
    for filename, office, url, expected_sha256 in SOURCES:
        path = ROOT/'data/raw'/filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256, f'Input changed: {filename}'
        with pdfplumber.open(path) as pdf:
            for number, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                assert len(tables) == 1, (filename, number)
                assert tables[0][0] == ['選舉區', '登記日期', '姓名', '推薦之政黨', '備註']
                for row in tables[0][1:]:
                    assert len(row) == 5 and all(row[:4]), row
                    county, date, name, party, note = row
                    rows.append(dict(county_city=county,registration_date_roc=date,
                        candidate_name=''.join(name.split()),party_recommendation_original=party,
                        source_note=note or '',office_type=office,source_file='data/raw/'+filename,
                        source_page=number,source_url=url))
    assert len(rows) == 81, len(rows)
    out = ROOT/'data/raw/cec_registration_2026_source_table.csv'
    with out.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(len(rows), hashlib.sha256(out.read_bytes()).hexdigest())

if __name__ == '__main__':
    extract()
