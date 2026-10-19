"""Capture official profile leads for the 2026-10-19 inventory.
Requires requests and beautifulsoup4. Four concurrent public GETs, no login.
Stops if the dated output folder already exists; preserves captured bytes.
County/name matches are leads and do not establish candidate identity.
"""
from pathlib import Path
import csv,json,requests,hashlib,time,concurrent.futures
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/raw/inventory_20261019';BASE.mkdir(exist_ok=False)
def read(n):return list(csv.DictReader((ROOT/'data/processed'/n).open(encoding='utf-8-sig')))
def norm(s):return s.replace('台','臺').replace('温','溫').replace(' ','').replace('　','')
council=read('council_candidates_2026_registration.csv');directory=read('current_councilors_20261018.csv')
idx={}
for r in directory:idx.setdefault((norm(r['county_city']),norm(r['official_name'])),[]).append(r)
jobs={}
for r in council:
 for d in idx.get((norm(r['county_city']),norm(r['candidate_name'])),[]):jobs[d['official_key']]=(d['profile_url'],d['official_name'],d['county_city'])
print('matched profile targets',len(jobs),flush=True)
jobs['cec_qualification']=('https://web.cec.gov.tw/central/article/65213','','')
jobs['cec_registration']=('https://web.cec.gov.tw/central/article/64733','','')
def fetch(item):
 key,(url,name,county)=item; record={'source_id':key,'url':url,'expected_name':name,'county_city':county,'captured_date':'2026-10-19','http_status':'','error':'','path':'','sha256':'','name_present':False,'education_raw':'','experience_raw':''}
 try:
  time.sleep(.2)
  r=requests.get(url,timeout=(10,25));record['http_status']=str(r.status_code)
  p=BASE/(key+'.html');p.write_bytes(r.content);record['path']=str(p.relative_to(ROOT));record['sha256']=hashlib.sha256(r.content).hexdigest()
  soup=BeautifulSoup(r.content,'html.parser');text=soup.get_text(' ',strip=True);record['name_present']=bool(name and norm(name) in norm(text))
  if r.status_code==200 and record['name_present']:
   for cap in soup.select('.essay .caption'):
    value=cap.parent.select_one('.p')
    if value and cap.get_text(strip=True) in ['學歷','簡歷']:
     record['education_raw' if cap.get_text(strip=True)=='學歷' else 'experience_raw']=value.get_text('\n',strip=True)
 except Exception as e:record['error']=str(e)
 return record
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for rec in pool.map(fetch,jobs.items()):
  records.append(rec)
  if len(records)%100==0:print('captured',len(records),flush=True)
(BASE/'capture_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('DONE',len(records),'education pages',sum(bool(r['education_raw']) for r in records),'errors',sum(bool(r['error']) for r in records),flush=True)
