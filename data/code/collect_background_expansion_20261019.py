from pathlib import Path
import json,hashlib,re,subprocess,concurrent.futures,urllib.parse
import pandas as pd
from requests.utils import requote_uri
R=Path(__file__).resolve().parents[2]
B=R/'data/raw/background_expansion_20261019';B.mkdir(exist_ok=True)
def norm(s):return re.sub(r'\s+','',s).replace('台','臺').replace('温','溫')
m=pd.read_csv(R/'data/processed/snapshots/pre_source_expansion_20261019/candidate_master_current.csv',dtype=str).fillna('')
c=pd.read_csv(R/'data/processed/snapshots/pre_source_expansion_20261019/council_background_20261019.csv',dtype=str).fillna('')
missing=set(c[c.moi_profile_url.eq('')&c.campaign_profile_url.eq('')].candidate_key)
idx={(norm(x.candidate_name),norm(x.electoral_district)):x.candidate_key for x in m.itertuples() if '議員' in x.office_type}
ed=json.loads((R/'data/raw/public_source_index_20261019/candidate-education.json').read_text())
jobs={};leads=[]
for person in ed['candidates']:
 race=person['role'].removesuffix('議員');key=idx.get((norm(person['name']),norm(race)))
 if key not in missing:continue
 for rec in person['records']:
  src=rec['source'];url=requote_uri(urllib.parse.urldefrag(src['url'])[0]);row=dict(candidate_key=key,candidate_name=person['name'],race=race,upstream_claim=rec['items'],upstream_source_url=src['url'],fetch_url=url,upstream_source_type=src['type'],upstream_source_year=rec.get('sourceYear'),upstream_note=rec.get('note',''))
  leads.append(row);jobs.setdefault(url,[]).append(key)
# Include candidate websites discovered in the mayor channel index, to recover primary social links.
ch=json.loads((R/'data/raw/public_source_index_20261019/candidate-channels.json').read_text())
for person in ch['candidates']:
 for link in person['links']:
  if link['kind'] not in ['campaign','website','official-website']:continue
  url=requote_uri(urllib.parse.urldefrag(link['url'])[0]);jobs.setdefault(url,[])
(B/'retrieval_plan.json').write_text(json.dumps({'generated_from':'public_source_index_20261019 fixed upstream snapshot','education_leads':leads,'urls':list(jobs)},ensure_ascii=False,indent=2))
mp=B/'capture_manifest.json';records=json.loads(mp.read_text()) if mp.exists() else []
for existing in records:
 if existing.get('path'):assert hashlib.sha256((R/existing['path']).read_bytes()).hexdigest()==existing['sha256']
seen={x['url'] for x in records}
def get(url):
 dest=B/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.source')
 proc=subprocess.run(['curl','-L','--silent','--show-error','--max-time','18','-w','%{http_code}\n%{content_type}\n%{url_effective}',url,'-o',str(dest)],text=True,capture_output=True)
 stats=proc.stdout.splitlines()
 r=dict(url=url,http_status=stats[0] if stats else '',content_type=stats[1] if len(stats)>1 else '',final_url=stats[2] if len(stats)>2 else '',return_code=proc.returncode,error=proc.stderr.strip(),captured_date='2026-10-19',candidate_keys=list(dict.fromkeys(jobs[url])),path='',sha256='',content_kind='no_saved_file')
 if dest.exists():
  body=dest.read_bytes();r.update(path=str(dest.relative_to(R)),sha256=hashlib.sha256(body).hexdigest(),content_kind='pdf' if body.startswith(b'%PDF') else 'html_or_other')
 return r
todo=[u for u in jobs if u not in seen]
print('leads',len(leads),'people',len(set(r['candidate_key'] for r in leads)),'fetches',len(jobs),'pending',len(todo),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 futures={pool.submit(get,url):url for url in todo}
 for f in concurrent.futures.as_completed(futures):
  records.append(f.result());temp=B/'capture_manifest.tmp';temp.write_text(json.dumps(records,ensure_ascii=False,indent=2));temp.replace(mp)
  if len(records)%10==0:print('captured',len(records),'last',records[-1]['http_status'],flush=True)
print('DONE',len(records),'PDF',sum(r['content_kind']=='pdf' for r in records),'200',sum(r['http_status']=='200' for r in records),flush=True)
