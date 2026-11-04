"""Conservative extraction of source observations; no missing-to-zero conversion."""
import re,json,datetime
from pathlib import Path
from bs4 import BeautifulSoup
from sex_focus_helpers_20261103 import norm,chinese_name,district_number,read_csv
RAW='data/raw/g1_g6_20261103/'
def plain(s):
 s=re.sub(r'<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>', '',s,flags=re.S|re.I)
 s=re.sub(r'<!--.*?-->','',s,flags=re.S)
 s=re.sub(r'\[\[([^\[\]]+)\]\]',lambda m:m[1].split('|')[-1],s)
 s=re.sub(r'\[https?://\S+\s+([^\]]+)\]',r'\1',s)
 s=re.sub(r'<br\s*/?>','\n',s,flags=re.I)
 s=BeautifulSoup(s,'html.parser').get_text()
 return s.replace("'''",'').replace("''",'').strip()
def infobox(text):
 m=re.search(r'\{\{\s*(?:Infobox|基礎情報)',text,re.I)
 if not m:return {}
 start=m.start();depth=0;link=0;parts=[];last=start+2;i=start
 while i<len(text)-1:
  pair=text[i:i+2]
  if pair=='{{':depth+=1;i+=2;continue
  if pair=='}}':
   depth-=1
   if depth==0:parts.append(text[last:i]);break
   i+=2;continue
  if pair=='[[':link+=1;i+=2;continue
  if pair==']]':link-=1;i+=2;continue
  if text[i]=='|' and depth==1 and link==0:parts.append(text[last:i]);last=i+1
  i+=1
 result={}
 for part in parts[1:]:
  if '=' in part:
   k,v=part.split('=',1);result[k.strip().lower().replace(' ','_')]=v.strip()
 return result

def load_pages(root):
 pages={};redirects={}
 manifest=json.loads((root/RAW/'download_manifest.json').read_text())
 for record in manifest:
  if 'wiki_batch' not in record['path'] or record['status']!=200:continue
  data=json.loads((root/record['path']).read_text())
  for item in data.get('query',{}).get('redirects',[]):redirects[item['from']]=item['to']
  for p in data.get('query',{}).get('pages',[]):
   if 'revisions' not in p:continue
   rv=p['revisions'][0];p=dict(title=p['title'],text=rv['slots']['main']['content'],revision_id=rv['revid'],timestamp=rv['timestamp'],source_file=record['path'],source_url='https://zh.wikipedia.org/w/index.php?oldid='+str(rv['revid']))
   p['box']=infobox(p['text']);pages[p['title']]=p
 return pages,redirects

def birth(box):
 s=box.get('birth_date',box.get('出生日期',''))
 m=re.search(r'\{\{(?:birth[_ ]date(?:[_ ]and[_ ]age)?|出生日期及年齡|bda|dob)[^|}]*\|\s*(\d{4})\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})',s,re.I)
 if not m:m=re.search(r'(19\d{2}|20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日',s)
 if not m:return ''
 try:return datetime.date(*map(int,m.groups())).isoformat()
 except ValueError:return ''

def past_elected(box):
 out=[]
 for k,v in box.items():
  if not re.fullmatch(r'(office|order)\d*',k):continue
  val=plain(v);suffix=re.search(r'\d*$',k)[0];date=plain(box.get('term_start'+suffix,''))
  y=re.search(r'(19\d{2}|20\d{2})',date)
  if y and int(y[1])<2026 and re.search('議員|立法委員|里長|村長|鄉長|鎮長|市長|縣長|鄉民代表|鎮民代表|市民代表',val) and not re.search('副市長|副縣長|代理|秘書|助理|辦公室|候選人|參選人',val):out.append(val+'；就任 '+date)
 return out

def linked_relatives(box):
 out=[]
 for field in ['parents','father','mother','spouse','children','relatives','父母','配偶']:
  raw=re.sub(r'<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>', '',box.get(field,''),flags=re.S|re.I)
  for m in re.finditer(r'\[\[([^\[\]]+)\]\]',raw):
   title=m[1].split('|')[0];display=m[1].split('|')[-1]
   if re.search('婚|離|中華|臺灣|台灣|中國|年|月|日|國民黨',title):continue
   if not re.fullmatch(r'[\u3400-\u9fff]{2,6}(?: \([^)]*\))?',title):continue
   context=plain(re.split(r'<br\s*/?>|\n|\[\[',raw[m.end():],maxsplit=1,flags=re.I)[0])
   if field in ['parents','father','mother','父母']:relation='父母';degree='1';kind='血親'
   elif field in ['spouse','配偶']:relation='配偶';degree='';kind='配偶'
   elif field=='children':relation='子女';degree='1';kind='血親'
   else:
    if re.search('堂|表',context):relation='堂表親（超出三親等）';degree='5' if re.search('叔|伯|姑|舅|姨|姪|侄|甥',context) else '4';kind='血親'
    elif re.search('小叔|小姑|大伯|大姑|嫂|弟媳|姊夫|姐夫|妹夫',context):relation='兄弟姊妹相關姻親';degree='2';kind='姻親'
    elif re.search('岳父|岳母|公公|婆婆',context):relation='配偶父母';degree='1';kind='姻親'
    elif re.search('（父|\(父|（母|\(母',context):relation='父母';degree='1';kind='血親'
    elif re.search('祖父|祖母|外公|外婆',context):relation='祖父母';degree='2';kind='血親'
    elif re.search('叔|伯|姑|舅|姨|姪|侄|甥',context):relation='三等旁系親屬';degree='3';kind='血親'
    elif re.search('兄|弟|姊|姐|妹|哥',context):relation='兄弟姊妹';degree='2';kind='血親'
    elif re.search('岳父|岳母|公公|婆婆',context):relation='配偶父母';degree='1';kind='姻親'
    else:relation='其他親屬待核';degree='';kind='待核'
   out.append(dict(relative_title=title,relative_name=display,relation=relation,degree=degree,kinship_type=kind,relation_field=field,relation_raw=plain(raw),eligible='1' if kind=='配偶' or degree in ['1','2','3'] else '0' if degree in ['4','5'] else ''))
 return out
