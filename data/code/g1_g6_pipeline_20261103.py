"""G1–G6 collection and G5 audit. Run through the companion pinned notebook."""
from pathlib import Path
from collections import defaultdict,Counter
import csv,json,re,hashlib,datetime
from bs4 import BeautifulSoup
from g1_g6_helpers_20261103 import *
from sex_focus_helpers_20261103 import historical_council_index
DATE='2026-11-04'
BASE='data/processed/'
SNAP=BASE+'snapshots/pre_g1_g6_20261103/'
def save(root,path,rows):
 assert rows and (root/path).resolve().is_relative_to((root/BASE).resolve())
 with (root/path).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 assert read_csv(root,path)==rows

def education_class(text):
 if text in ['博士','碩士']:return '研究所'
 if text=='大學':return '大學'
 if text in ['專科','高中(職)','高中(職)以下']:return '大學以下'
 lines=re.split(r'\n|\||；|;',plain(text))
 complete=[x for x in lines if not re.search('肄業|在學|就讀|進修|博士班|碩士班|休學|未畢業|撤銷|研習|結業',x)]
 if any(re.search('博士|碩士',x) for x in complete):return '研究所'
 if any(re.search('學士|(?:大學|學院).*(?:系|學程).*畢業',x) for x in complete):return '大學'
 return ''

def run(root):
 root=Path(root);pins=json.loads((root/'data/code/g1_g6_inputs_20261103.json').read_text())
 for p,h in pins.items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
 master=read_csv(root,SNAP+'candidate_master_current.csv');fields=read_csv(root,SNAP+'candidate_fields_current.csv');background=read_csv(root,SNAP+'council_background_20261019.csv')
 fi={(r['candidate_key'],r['field']):r for r in fields};bi={r['candidate_key']:r for r in background}
 mayor={r['candidate_key']:r for r in read_csv(root,BASE+'candidates_2026_enriched.csv')}
 sex={r['candidate_key']:r for r in read_csv(root,BASE+'council_sex_current.csv')}
 history=read_csv(root,BASE+'candidate_all_office_history.csv');hi=defaultdict(list)
 for r in history:
  if r['identity_match_status']=='dob_corroborated_by_media':hi[r['candidate_key']].append(r)
 pages,redirects=load_pages(root);links={r['candidate_key']:r for r in json.loads((root/'data/code/g1_g6_person_links_20261103.json').read_text())}
 hindex,_=historical_council_index(root)
 cna={};soup=BeautifulSoup((root/RAW/'cna_mayors.html').read_bytes(),'html.parser')
 for d in soup.select('div.dictionary-box'):
  name=d.select_one('.dictionary-title').get_text(strip=True);vals={}
  for li in d.find_all('li'):
   t=li.get_text(' ',strip=True)
   if '：' in t:k,v=t.split('：',1);vals[k]=v
  cna[name]=vals
 # Family facts are published observations, not inferred from surnames or photos.
 family=[]
 for key,link in links.items():
  p=pages[link['title']]
  for rel in linked_relatives(p['box']):
   q=pages.get(redirects.get(rel['relative_title'],rel['relative_title']));off=past_elected(q['box']) if q else []
   # G6 office evidence does not require a complete term date; preserve missing dates explicitly.
   if not off and q:
    off=[plain(v)+'；期間待補' for k,v in q['box'].items() if re.fullmatch('(office|order)\\d*',k) and re.search('議員|立法委員|縣長|鄉長|鎮長|市長|里長|村長|鄉民代表|國民大會代表',plain(v)) and not re.search('候選人|參選人|助理|秘書|副市長|副縣長',plain(v))]
   # No office found means unknown, not a negative political-family finding.
   status='secondary_relationship_and_public_office' if off and rel['eligible']=='1' else 'outside_three_degrees' if rel['eligible']=='0' else 'relative_office_or_relation_pending'
   family.append(dict(candidate_key=key,candidate_name=link['candidate_name'],relative_name=rel['relative_name'],relationship=rel['relation'],degree=rel['degree'],kinship_type=rel['kinship_type'],in_scope=rel['eligible'],relative_public_office=' / '.join(off),office_type='民選職務（來源記載）' if off else '',relationship_text=rel['relation_raw'],relationship_source_url=p['source_url'],relationship_source_file=p['source_file'],office_source_url=q['source_url'] if q else '',office_source_file=q['source_file'] if q else '',source_tier='secondary_wikipedia',review_status=status,checked_date=DATE))
 for rel in json.loads((root/'data/code/g1_g6_family_review_20261103.json').read_text()):
  row=dict(candidate_key=rel['candidate_key'],candidate_name=rel['candidate_name'],relative_name=rel['relative_name'],relationship=rel['relation'],degree=rel['degree'],kinship_type=rel['kinship_type'],in_scope='1',relative_public_office=rel['relative_office'],office_type=rel['office_type'],relationship_text=rel['source_text'],relationship_source_url=rel['source_url'],relationship_source_file=rel['source_file'],office_source_url=rel['source_url'],office_source_file=rel['source_file'],source_tier=rel['source_tier'],review_status='secondary_relationship_and_public_office',checked_date=DATE)
  family=[x for x in family if (x['candidate_key'],x['relative_name'])!=(row['candidate_key'],row['relative_name'])];family.append(row)
 # Independently preserved reporting corroborates five reviewed parent relationships.
 corroborators={('蔣萬安','蔣孝嚴'):('chiang_family.html','https://www.cna.com.tw/news/aipl/201711010159.aspx'),('柯志恩','柯文福'):('ko_family.html','https://news.tvbs.com.tw/politics/1871102'),('何欣純','林淑滿'):('ho_family_news.html','https://www.knews.com.tw/news/7888AEFF180E33CB34889F5584F660D3'),('周春米','周輝煌'):('chou_family_news.html','https://news.tvbs.com.tw/politics/1837298'),('魏平政','魏陳春惠'):('wei_prior_election.html','https://www.mirrormedia.mg/story/20260417inv002')}
 for row in family:
  row['corroborating_source_url']='';row['corroborating_source_file']=''
  pair=(row['candidate_name'],row['relative_name'])
  if pair in corroborators:
   file,url=corroborators[pair];text=BeautifulSoup((root/RAW/file).read_bytes(),'html.parser').get_text(' ',strip=True)
   assert all(n in text for n in pair),pair
   row['corroborating_source_url']=url;row['corroborating_source_file']=RAW+file;row['source_tier']='secondary_with_separate_news_corroboration'
 families=defaultdict(list)
 for r in family:
  if r['in_scope']=='1' and r['relative_public_office']:families[r['candidate_key']].append(r)
 g5_reviews={x['candidate_key']:x for x in json.loads((root/'data/code/g1_g6_g5_source_review_20261104.json').read_text())}
 for x in g5_reviews.values():
  text=(root/x['source_file']).read_text(encoding='utf-8-sig')
  if x['source_file'].endswith(('.html','.source')):text=BeautifulSoup(text,'html.parser').get_text(' ',strip=True)
  assert all(norm(token) in norm(text) for token in x['assert_tokens'])
 first_reviews=json.loads((root/'data/code/g1_g6_first_time_review_20261104.json').read_text())
 first_by_key={x['candidate_key']:x for x in first_reviews if x['decision']=='accepted_explicit_first_time_report'}
 for x in first_by_key.values():
  text=BeautifulSoup((root/x['source_file']).read_bytes(),'html.parser').get_text(' ',strip=True)
  assert x['assert_phrase'] in text and x['candidate_name'] in text
 result=[];audit=[];evidence=[];issues=[];pending_matches=[]
 for m in master:
  key=m['candidate_key'];name=m['candidate_name'];b=bi.get(key,{});old=mayor.get(key,{});link=links.get(key);p=pages[link['title']] if link else None;box=p['box'] if p else {};wb=birth(box)
  prior={fld:fi[key,fld] for fld in ['birth_date','sex','education','first_time_any_office','political_family']}
  birthval=prior['birth_date']['existing_value'];birthsource=prior['birth_date']['evidence'];birthtier='prior_evidence_retained' if birthval else ''
  cv=cna.get(name,{}) if '議員' not in m['office_type'] else {};cb='';hit=re.search(r'(19\d{2}|20\d{2})年(\d{1,2})月(\d{1,2})日',cv.get('生日',cv.get('出生','')))
  if hit:cb=datetime.date(*map(int,hit.groups())).isoformat()
  for sourceval,url in [(cb,'https://www.cna.com.tw/news/aipl/202610275002.aspx'),(wb,p['source_url'] if p else '')]:
   if birthval and sourceval and sourceval!=birthval:issues.append(dict(candidate_key=key,candidate_name=name,field='G1_birth_date',previous_value=birthval,observed_value=sourceval,source_url=url,note='保留原值；來源不一致，未自動裁定'))
  if not birthval and cb:birthval=cb;birthsource='https://www.cna.com.tw/news/aipl/202610275002.aspx';birthtier='media_2026_explicit_birth_date'
  if not birthval and wb:birthval=wb;birthsource=p['source_url'];birthtier='secondary_wikipedia_explicit_birth_date'
  birthyear=birthval[:4] if re.match(r'^\d{4}-\d{2}-\d{2}$',birthval) else old.get('media_birth_year','')
  if not birthsource and birthyear:birthsource=old.get('birth_date_source_url','');birthtier='prior_media_birth_year'
  age=str(2026-int(birthyear)) if birthyear and birthyear.isdigit() else ''
  if age:assert 18<=int(age)<=110,(name,birthyear)
  edu=prior['education']['existing_value'];edusource=prior['education']['evidence'];edutier='prior_education_retained' if edu else ''
  we=plain(box.get('educate',box.get('education',box.get('alma_mater',''))))
  if not edu and cv.get('學歷'):edu=cv['學歷'];edusource='https://www.cna.com.tw/news/aipl/202610275002.aspx';edutier='media_2026_education_profile'
  if not edu and we:edu=we;edusource=p['source_url'];edutier='secondary_wikipedia_education_profile'
  # Official historical link is accepted only if previously reviewed, or birth date agrees with a separately linked biography.
  accepted_h=None
  if b.get('history_source_file') and b.get('history_source_row') and b.get('history_identity_review') and not re.search('待|未找到',b['history_identity_review']):
   file=b['history_source_file'];rownum=int(b['history_source_row']);raw=list(csv.reader((root/file).open(encoding='utf-8-sig')))[rownum-1]
   assert len(raw)==16
   accepted_h=dict(source_file=file,source_row=str(rownum),source_name=raw[6],birth_roc=raw[9],sex={'1':'男','2':'女'}[raw[8]],education=raw[12],identity='prior_reviewed_history_link')
  if key in bi and accepted_h is None:
   hs=hindex[(norm(m['county_city']),district_number(m['electoral_district']),chinese_name(name))]
   if len(hs)==1:
    h=hs[0];roc=h['birth_roc'];hb=f'{int(roc[:3])+1911:04d}-{roc[3:5]}-{roc[5:7]}' if len(roc)==7 else ''
    if hb and wb and hb==wb:
     raw=list(csv.reader((root/h['source_file']).open(encoding='utf-8-sig')))[int(h['source_row'])-1];accepted_h=dict(**h,education=raw[12],identity='same_name_county_district_and_biography_birth_date')
    else:pending_matches.append(dict(candidate_key=key,candidate_name=name,source_file=h['source_file'],source_row=h['source_row'],historical_birth_date=hb,identity_status='same_name_county_district_only_not_promoted'))
  historical_edu=accepted_h['education'] if accepted_h else old.get('education_latest_cec','')
  historical_edu_source=(accepted_h['source_file']+':'+accepted_h['source_row']) if accepted_h else ('data/processed/candidates_2026_enriched.csv; year='+old.get('education_latest_cec_year','') if historical_edu else '')
  if not edu and historical_edu:edu=historical_edu;edusource=historical_edu_source;edutier='official_historical_declared_level'
  educlass=education_class(edu);classsource=edusource;classnote='明載學位或歷史官方級別；非學位認證'
  if not educlass and historical_edu:educlass=education_class(historical_edu);classsource=historical_edu_source;classnote='採歷史官方級別；最新原文未足以判定完成程度'
  if not educlass:classnote='學歷原文保留；完成程度或三級分類待核'
  g5=prior['first_time_any_office']['existing_value'];oldg5=g5;g5source=prior['first_time_any_office']['evidence'];g5detail='';auditstatus='unknown_no_lifetime_first_claim';exampleyear=''
  if accepted_h:
   g5='0';g5source=accepted_h['source_file']+':'+accepted_h['source_row'];g5detail='2022官方議員參選紀錄；'+accepted_h['identity'];exampleyear='2022';auditstatus='official_historical_record_located_identity_supported'
  elif hi[key]:
   h=min(hi[key],key=lambda x:int(x['election_year']));g5='0';g5source=h['source_file']+':'+h['source_row'];g5detail=h['election_context']+'；既有生日佐證身分連結';exampleyear=h['election_year'];auditstatus='official_historical_record_located_identity_supported'
   raw=list(csv.reader((root/h['source_file']).open(encoding='utf-8-sig')))[int(h['source_row'])-1];assert raw[6].strip()==h['candidate_name'].strip(),(name,h)
  elif past_elected(box):
   g5='0';g5source=p['source_url'];g5detail=' / '.join(past_elected(box));auditstatus='secondary_prior_elected_office_located'
   ys=re.findall(r'(?:19|20)\d{2}',g5detail);exampleyear=min(ys) if ys else ''
  elif g5=='0':
   auditstatus='prior_evidence_retained_further_source_recheck';g5detail=prior['first_time_any_office']['status']+'；'+prior['first_time_any_office']['note']
  if key in g5_reviews:
   review=g5_reviews[key];g5='0';g5source=review['source_file']+'; '+review['source_locator'];g5detail=review['evidence'];exampleyear=review['prior_year'];auditstatus=review['source_tier']
  if name=='蔣萬安' and m['county_city']=='臺北市' and '議員' not in m['office_type']:
   source=RAW+'chiang_ly_2016.html';text=BeautifulSoup((root/source).read_bytes(),'html.parser').get_text(' ',strip=True)
   assert '蔣萬安' in text and '2016' in text and ('第9屆' in text or '第 9 屆' in text)
   g5='0';exampleyear='2016';g5source='https://www.ly.gov.tw/Pages/List.aspx?nodeid=1902';g5detail='立法院第9屆委員資料：2016/02/01至2020/01/31，臺北市第3選舉區；0=非首次參選任何民選公職';auditstatus='official_profile_rechecked_this_run'
  if key in first_by_key:
   review=first_by_key[key]
   assert g5!='0', (name, 'first-time claim conflicts with accepted past record')
   g5='1';g5source=review['source_url'];g5detail=review['source_excerpt']+'；'+review['note'];auditstatus='explicit_first_time_report_not_exhaustive_archive_proof'
  assert g5 in {'','0','1'}
  g5label={'0':'非首次參選任何民選公職','1':'首次參選任何民選公職','':'未知／未核實'}[g5]
  fam=families[key];g6='1' if fam else '';g6label='有三親等內或配偶公職來源記載' if fam else '未知／尚無足夠來源；不是0'
  famsource=' | '.join(dict.fromkeys(x['relationship_source_url'] for x in fam));famdetail='；'.join(x['relative_name']+'（'+x['relationship']+'）：'+x['relative_public_office'] for x in fam)
  party=m['party_registration_raw'];partyclass='無黨籍／未經政黨推薦' if re.search('無黨|無黨籍|無推薦|^無$|^無黨籍及未經政黨推薦$',party) else '國民黨' if '中國國民黨' in party else '民進黨' if '民主進步黨' in party else '民眾黨' if re.search('台灣民眾黨|臺灣民眾黨',party) else '其他政黨' if party else ''
  sexval=prior['sex']['existing_value'];sextier=sex[key]['source_tier'] if key in sex else old.get('sex_source_tier','prior_evidence_retained');sexsource=sex[key]['source_url'] if key in sex else prior['sex']['evidence']
  result.append(dict(candidate_key=key,candidate_name=name,county_city=m['county_city'],office_type=m['office_type'],electoral_district=m['electoral_district'],G1_age_2026_minus_birth_year=age,birth_date=birthval,birth_year=birthyear,G1_source_tier=birthtier,G1_source=birthsource,G2_sex=sexval,G2_source_tier=sextier,G2_source=sexsource,G3_education_level=educlass,education_raw=edu,G3_source=classsource,G3_note=classnote,education_source_tier=edutier,education_historical_level=historical_edu,G4_party=partyclass,party_registration_raw=party,G4_source=m['registration_source'],G4_note='依登記推薦政黨分類；無推薦不等於已查證本人無黨籍',G5_first_time_any_elected_office=g5,G5_label=g5label,G5_prior_election_year_example=exampleyear,G5_evidence=g5detail,G5_source=g5source,G5_audit_status=auditstatus,G6_political_family=g6,G6_label=g6label,G6_evidence=famdetail,G6_source=famsource,G6_evidence_tier='published_secondary_relationships_see_family_table' if fam else '',source_conflict_flag='1' if any(x['candidate_key']==key for x in issues) or (key in sex and sex[key]['exclude_from_unqualified_2026_analysis']=='1') else '0',checked_date=DATE))
  audit.append(dict(candidate_key=key,candidate_name=name,office_type=m['office_type'],previous_value=oldg5,audited_value=g5,meaning=g5label,prior_election_year_example=exampleyear,evidence=g5detail,source=g5source,audit_status=auditstatus,changed='1' if g5!=oldg5 else '0',note='例示年份不是終生最早參選年份；首次選本職與首次參選任何公職不同。',checked_date=DATE))
  vals=[('G1',age,birthsource,birthtier),('G2',sexval,sexsource,sextier),('G3',educlass,classsource,classnote),('G4',partyclass,m['registration_source'],'official_registration_party'),('G5',g5,g5source,auditstatus),('G6',g6,famsource,'secondary_relationships' if fam else 'unknown_not_zero')]
  for fld,v,src,tier in vals:evidence.append(dict(candidate_key=key,candidate_name=name,field=fld,value=v,source=src,status=tier,checked_date=DATE))
 assert len(result)==1583 and len({x['candidate_key'] for x in result})==1583 and len(evidence)==1583*6
 assert sum(x['G5_first_time_any_elected_office']=='1' for x in result)==len(first_by_key)
 assert all(x['G6_political_family']!='0' for x in result), 'Absence of family evidence is unknown'
 outputs={BASE+'candidates_g1_g6_current.csv':result,BASE+'candidate_g5_audit_20261103.csv':audit,BASE+'candidate_g6_family_evidence_20261103.csv':family,BASE+'candidate_g1_g6_field_evidence_20261103.csv':evidence,BASE+'candidate_g1_g6_source_conflicts_20261103.csv':issues,BASE+'candidate_g1_g6_identity_pending_20261103.csv':pending_matches}
 gaps=[]
 for r in result:
  for field,col in [('G1','G1_age_2026_minus_birth_year'),('G2','G2_sex'),('G3','G3_education_level'),('G4','G4_party'),('G5','G5_first_time_any_elected_office'),('G6','G6_political_family')]:
   if not r[col]:gaps.append(dict(candidate_key=r['candidate_key'],candidate_name=r['candidate_name'],county_city=r['county_city'],office_type=r['office_type'],field=field,status='unknown_not_zero',next_step={'G1':'當屆公報出生年／本人公開履歷','G2':'當屆官方性別欄','G3':'最高已完成學歷明載資料；區分肄業／在學','G4':'官方登記政黨','G5':'跨公職歷史及當屆首次參選明確敘述；排除同名','G6':'三親等／配偶關係與公職證據；不得用查無結果填0'}[field]))
 outputs[BASE+'candidate_g1_g6_remaining_worklist_20261103.csv']=gaps
 outputs[BASE+'candidate_g5_first_time_lead_review_20261104.csv']=first_reviews
 checks={}
 for path,rows in outputs.items():
  save(root,path,rows);checks[path]=dict(rows=len(rows),columns=len(rows[0]),sha256=hashlib.sha256((root/path).read_bytes()).hexdigest())
 summary=dict(candidates=1583,g5_first_time_reported=len(first_by_key),coverage={f:sum(bool(r[c]) for r in result) for f,c in [('G1','G1_age_2026_minus_birth_year'),('G2','G2_sex'),('G3','G3_education_level'),('G4','G4_party'),('G5','G5_first_time_any_elected_office'),('G6','G6_political_family')]},g5_prior_nonfirst=sum(x['previous_value']=='0' for x in audit),g5_new_nonfirst=sum(x['previous_value']=='' and x['audited_value']=='0' for x in audit),g5_audit_status=dict(Counter(x['audit_status'] for x in audit)),family_rows=len(family),source_conflicts=len(issues),outputs=checks)
 (root/BASE/'candidate_g1_g6_verification_20261103.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');return summary
