"""Re-download recorded public source URLs into a NEW raw snapshot directory.

Example: python data/code/download_candidate_sources.py --snapshot 20261018
Requires curl. Existing snapshots are never overwritten. Does not log into sites
or bypass access restrictions; failed requests remain failures in the manifest.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshot',required=True,help='YYYYMMDD; must be a new directory')
    args=parser.parse_args()
    datetime.datetime.strptime(args.snapshot,'%Y%m%d')
    root=Path(__file__).resolve().parents[2]
    destination=root/'data/raw'/('recollection_'+args.snapshot)
    destination.mkdir(exist_ok=False)
    records=[]
    for name in ['ly_profile_capture_manifest.json','candidate_website_capture_manifest.json','extra_campaign_capture_manifest.json']:
        records.extend(json.loads((root/'data/raw'/name).read_text()))
    results=[]; seen=set()
    for item in records:
        if item['url'] in seen:continue
        seen.add(item['url'])
        path=destination/f'{len(results)+1:03d}.source'
        result={'candidate_name':item['candidate_name'],'url':item['url']}
        command=['curl','-L','--fail','--max-time','45','--silent','--show-error',item['url'],'-o',str(path)]
        run=subprocess.run(command,capture_output=True,text=True)
        result.update(status='downloaded' if run.returncode==0 else 'failed',return_code=run.returncode)
        if run.returncode==0:
            result.update(path=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        else:result['error']=run.stderr.strip()
        results.append(result)
    (destination/'capture_manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(f'Saved {len(results)} attempts. Inspect content and version before updating notebook input hashes.')

if __name__=='__main__':main()
