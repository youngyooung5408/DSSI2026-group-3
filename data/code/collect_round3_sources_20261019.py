"""Capture public, linked candidate sources without login or access-control bypass.
Only explicit URLs and links found on captured official/party pages are fetched.
Preserves raw bytes; resume skips files recorded with matching SHA-256.
"""
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests,hashlib,json,subprocess,csv,time
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/raw/round3_20261019'
BASE.mkdir(exist_ok=True)
MANIFEST=BASE/'capture_manifest.json'
records=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else []
seen={r['url']:r for r in records}
def save_manifest():
 p=BASE/'capture_manifest.tmp';p.write_text(json.dumps(records,ensure_ascii=False,indent=2));p.replace(MANIFEST)
def fetch(url,kind='public_source',parent=''):
 if url in seen:
  r=seen[url]
  if r.get('path'):assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
  return r
 key=hashlib.sha256(url.encode()).hexdigest()[:20];p=BASE/(key+'.source')
 # curl verifies TLS using the platform trust store; no insecure or credential flags.
 run=subprocess.run(['curl','-L','--silent','--show-error','--max-time','25','-w','%{http_code}',url,'-o',str(p)],capture_output=True,text=True)
 rec=dict(url=url,kind=kind,linked_from=parent,captured_date='2026-10-19',http_status=run.stdout,return_code=str(run.returncode),error=run.stderr.strip(),path='',sha256='')
 if p.exists():rec.update(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 records.append(rec);seen[url]=rec;save_manifest();print(len(records),rec['http_status'],url,flush=True);return rec
def soup(rec):
 return BeautifulSoup((ROOT/rec['path']).read_bytes(),'html.parser') if rec.get('path') and rec['http_status']=='200' else None
def collect():
 seeds=[
 ('https://teamtaiwan.dpp.org.tw/','party_home'),
 ('https://teamtaiwan.dpp.org.tw/councilor','party_candidates'),
 ('https://www.tpp.org.tw/2026election/','party_candidates'),
 ('https://www.tpp.org.tw/election2026/candidates.php','party_candidates'),
 ('https://2026.kmtks.org.tw/','party_candidates'),
 ('https://www1.kmt.org.tw/page.aspx?mid=40','party_candidates'),
 ('https://www.taiwangogo.tw/candidates/','alliance_candidates')]
 for url,kind in seeds:
  rec=fetch(url,kind);s=soup(rec)
  if s is None:continue
  for el in s.find_all('script',src=True):
   src=urljoin(url,el['src'])
   if urlparse(src).netloc==urlparse(url).netloc and ('script_' in src or 'candidate' in src):fetch(src,'linked_candidate_data',url)
  if 'taiwangogo.tw' in url:
   for el in s.find_all('a',href=True):
    href=urljoin(url,el['href'])
    if urlparse(href).netloc==urlparse(url).netloc and '/candidates/' in urlparse(href).path and href.rstrip('/')!=url.rstrip('/'):fetch(href,'alliance_candidate_profile',url)
 if __name__=='__main__':pass
if __name__=='__main__':collect()
