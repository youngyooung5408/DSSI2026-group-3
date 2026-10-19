"""Preserve ordinary public HTTP attempts for candidate identity corroboration.
No login, retries around blocking, or extraction of private account data.
"""
from pathlib import Path
import requests,json,hashlib,concurrent.futures
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/raw/identity_followup_20261019';OUT.mkdir(exist_ok=True)
PLAN=[
 ('林慧欣','https://newtalk.tw/news/view/2026-02-10/1019657'),
 ('鄭東元','https://hoomedia.com.tw/2026/09/04/165433/'),
 ('李柏融','https://tw.news.yahoo.com/高雄二選區-2無黨攪亂藍綠版圖-201000262.html/'),
 ('柳淑芳','https://tw.news.yahoo.com/高雄十大傳說-舉牌姊-將八度參選-柳淑芳-護台灣此生無悔-013959931.html'),
 ('陳惠君','https://more-news.tw/714185/'),
 ('童燕珍','https://www.cna.com.tw/news/aloc/202604220132.aspx'),
 ('童燕珍','https://news.pchome.com.tw/living/cna/20260422/index-17768349953142118009.html'),
 ('蘇致榮','https://newtalk.tw/news/view/2026-02-10/1019604'),
 ('蘇致榮、徐尚賢','https://udn.com/vote2026/story/124652/9652381'),
 ('徐尚賢','https://www.kingtop.com.tw/detail.php?id=31299&type=popular'),
 ('湯茹婷','https://news111.com.tw/news/47/12852'),
 ('洪村銘','https://news111.com.tw/news/48/10939'),
 ('陳若翠','https://www.300c3.org.tw/uninews_view.php?lang=TS&new_sn=117624')]
def get(item):
 name,u=item;path=OUT/(hashlib.sha256(u.encode()).hexdigest()[:20]+'.html')
 try:
  q=requests.get(u,timeout=20);path.write_bytes(q.content)
  return {'candidate_name':name,'url':u,'status':str(q.status_code),'content_type':q.headers.get('Content-Type',''),'final_url':q.url,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(q.content).hexdigest(),'checked_date':'2026-10-19'}
 except requests.RequestException as e:return {'candidate_name':name,'url':u,'status':'request_failed','path':'','error':str(e),'checked_date':'2026-10-19'}
if __name__=='__main__':
 # A completed capture is not silently replaced by a later request.
 target=OUT/'manifest.json'
 if target.exists():raise SystemExit('Capture already exists; inspect or choose a new version instead of overwriting raw bytes.')
 records=list(concurrent.futures.ThreadPoolExecutor(max_workers=3).map(get,PLAN))
 target.write_text(json.dumps(records,ensure_ascii=False,indent=2))
 for a in records:print(a['candidate_name'],a['status'],a['url'])
