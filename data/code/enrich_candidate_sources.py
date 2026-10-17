"""Reproduce candidate background/evidence tables from pinned local snapshots.

Called by enrich_candidates_2026.ipynb. No downloads, model fitting, or imputation.
Source education is a declaration, not independent credential authentication.
"""
from pathlib import Path
import csv, datetime as dt, hashlib, io, json, re
from urllib.parse import urlparse, urljoin
import pandas as pd
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
CEC='https://db.cec.gov.tw/'
CNA='https://www.cna.com.tw/news/aipl/202609045002.aspx'
QUAL='https://web.cec.gov.tw/central/article/65213'
PDFURL='https://web.cec.gov.tw/api/file/9cdda387-4bb9-4939-8825-1d1a8cd66684.pdf'

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path): return pd.read_csv(path,dtype=str,keep_default_na=False)
def text_soup(path): return BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
def norm(s): return re.sub(r'\s+','',s).replace('台','臺')
def iso_roc(raw):
    raw=raw.strip().lstrip("'")
    if not re.fullmatch(r'\d{7}',raw): return ''
    try: return dt.date(int(raw[:3])+1911,int(raw[3:5]),int(raw[5:])).isoformat()
    except ValueError: return ''
def iso_media(raw):
    m=re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日',raw.strip())
    if not m:return ''
    try:return dt.date(*map(int,m.groups())).isoformat()
    except ValueError:return ''

def build(expected_inputs):
    for relative,expected in expected_inputs.items():
        path=(ROOT/relative).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(),relative
        assert digest(path)==expected, f'Input changed: {relative}'
    base=read_csv(ROOT/'data/processed/candidates_2026_registration.csv')
    assert len(base)==81 and base.candidate_key.is_unique
    byname={r.candidate_name:r.candidate_key for r in base.itertuples()}
    observations=[]; campaigns=[]; texts=[]; issues=[]
    def observe(name,field,value,kind,url,file,locator='',context='',status='source_observation'):
        if name in byname and value:
            observations.append(dict(candidate_key=byname[name],candidate_name=name,field=field,value=str(value),source_type=kind,source_url=url,source_file=file,source_locator=locator,source_time_context=context,captured_date='2026-10-17',verification_status=status))

    # Supplementary media dictionary: do not treat party membership or old current-office labels as official.
    cnafile='data/raw/cna_2026_candidates_supplement.html'
    media={}
    for box in text_soup(ROOT/cnafile).select('.dictionary-box'):
        title=box.select_one('.dictionary-title')
        if not title:continue
        name=title.get_text(strip=True)
        if name not in byname:continue
        fields={}
        for li in box.select('.news-dic-text li'):
            line=li.get_text(' ',strip=True)
            if '：' not in line:continue
            label,value=line.split('：',1); fields[label]=value
            observe(name,'media_'+label,value,'media_supplement',CNA,cnafile,'.dictionary-box[data-box="'+box.get('data-box','')+'"]','CNA 2026-09-19 update; supplementary, can contain stale entries','supplementary_not_primary')
        media[name]=fields

    # Official current legislature profiles; social share buttons are excluded.
    for item in json.loads((ROOT/'data/raw/ly_profile_capture_manifest.json').read_text()):
        if item['status']!='downloaded':continue
        name=item['candidate_name']; soup=text_soup(ROOT/item['path'])
        text=soup.get_text(' ',strip=True)
        assert name in text and soup.select_one('.info-right'),name
        sex=re.search(r'性別[：:]\s*([男女])',text)
        if sex:observe(name,'sex',sex[1],'official_profile',item['url'],item['path'],'性別','11th legislature; captured 2026-10-17')
        for label,field in [('學歷','education_profile'),('經歷','experience_profile')]:
            node=soup.find('h4',string=lambda s:s and s.strip()==label)
            if node:
                ul=node.find_next_sibling('ul')
                value='；'.join(li.get_text(' ',strip=True) for li in ul.find_all('li',recursive=False)) if ul else ''
                observe(name,field,value,'official_profile',item['url'],item['path'],label,'Official profile as captured; underlying declaration date may precede 2026')
        observe(name,'prior_elected_office','立法委員（第11屆）','official_profile',item['url'],item['path'],'姓名、屆別及到職日期','Historical service evidence; does not imply still in office')
        campaigns.append(dict(candidate_key=byname[name],candidate_name=name,source_kind='official_profile',url=item['url'],discovered_on=item['url'],source_file=item['path'],verification_status='official_institution_profile',content_capture_status='saved_html'))

    # Education and incumbent observations from inspected government biographies.
    manual_education={
        '蔣萬安':'美國賓夕法尼亞大學法學院法律博士；國立政治大學法律系、外交系雙學士',
        '許淑華':'逢甲大學經營管理碩士畢',
        '鍾東錦':'南埔國民小學；興華國民中學；大成高級中學；中華大學企業管理系',
        '謝國樑':'國立政治大學法律學碩士；美國麻省理工學院科技管理學碩士；美國南加州大學社會系學士；二信中學；聖心小學',
        '高虹安':'美國辛辛那提大學機械工程博士；國立臺灣大學資訊工程系碩士；國立臺灣師範大學資訊教育學士',
        '李四川':'國立臺北科技大學電機研究所碩士',
    }
    manifests=['candidate_website_capture_manifest.json','extra_campaign_capture_manifest.json']
    captures=[]
    for mf in manifests:captures.extend(json.loads((ROOT/'data/raw'/mf).read_text()))
    for item in captures:
        if item['status']!='downloaded' or item['path'].endswith('.pdf'):continue
        name=item['candidate_name']; soup=text_soup(ROOT/item['path']); content=soup.get_text(' ',strip=True)
        if name not in content:
            issues.append(dict(candidate_key=byname[name],candidate_name=name,field='download',issue='Downloaded page did not contain candidate name; excluded',source_file=item['path']));continue
        kind=item['kind']; url=item['url']; file=item['path']
        if name in manual_education and kind in ['government_profile','regional_government_profile','party_profile']:
            if '學歷' in content:
                observe(name,'education_profile',manual_education[name],kind,url,file,'學歷（人工讀取該段）','As published on government/party site; publication may be older')
        if kind in ['government_profile','regional_government_profile']:
            if name in ['蔣萬安','許淑華','鍾東錦','謝國樑','高虹安']:
                observe(name,'incumbency','現任',kind,url,file,'首長姓名與職稱','Government website capture 2026-10-17; subject to later personnel changes')
        if kind.startswith('candidate_') or kind=='party_profile':
            campaigns.append(dict(candidate_key=byname[name],candidate_name=name,source_kind=kind,url=url,discovered_on=url,source_file=file,verification_status='self_identified_campaign_site' if kind.startswith('candidate_') else 'official_party_profile',content_capture_status='saved_html'))
            # Only campaign/self-published or personal party links, never municipal footer accounts.
            for anchor in soup.find_all('a',href=True):
                href=urljoin(url,anchor['href']); host=urlparse(href).netloc.lower(); path=urlparse(href).path
                platform=next((v for v in ['facebook.com','instagram.com','youtube.com','threads.net','threads.com','page.line.me'] if host==v or host.endswith('.'+v)),None)
                if not platform or any(token in href for token in ['sharer','share.php','/dialog/','/login','intent/']):continue
                if path in ['','/','#']:continue
                is_post=('/share/p/' in path or '/posts/' in path or '/reel/' in path or 'story_fbid=' in href)
                campaigns.append(dict(candidate_key=byname[name],candidate_name=name,source_kind='linked_post' if is_post else platform,url=href,discovered_on=url,source_file=file,verification_status='linked_by_candidate_site' if kind.startswith('candidate_') else 'linked_by_party_profile',content_capture_status='link_only_platform_content_not_downloaded'))
            if kind.startswith('candidate_'):
                body=soup.find('main') or soup.find('article') or soup.body or soup
                for node in body(['script','style','nav','header','footer','form','button']):node.decompose()
                seen=set()
                for idx,node in enumerate(body.find_all(['h1','h2','h3','h4','p','li'])):
                    text=node.get_text(' ',strip=True)
                    if len(text)<12 or text in seen:continue
                    seen.add(text)
                    texts.append(dict(candidate_key=byname[name],candidate_name=name,source_url=url,source_file=file,source_kind=kind,block_number=str(idx),html_tag=node.name,text_original=text,captured_date='2026-10-17',published_date='',coding_status='unlabelled_source_block_not_independent_policy_item'))

    # Visually checked party-list bulletin cells (12-page official original retained).
    pdfclaims=[('沈伯洋','1982-06-07','男',9),('蕭文乾','1974-09-27','男',9),('吳宗憲','1971-09-27','男',10),('張啓楷','1962-12-21','男',11),('張靜','1956-05-27','男',11)]
    for name,born,sex,page in pdfclaims:
        for field,value in [('birth_date',born),('sex',sex),('prior_elected_office','2024 不分區立法委員候選人')]:
            observe(name,field,value,'official_bulletin',PDFURL,'data/raw/cec_2024_party_list_bulletin.pdf','page '+str(page)+'; candidate personal-information row','2024-01-13 election','visually_checked_pdf_cell')

    # CEC qualification announcement is client-rendered. Indexed official excerpts
    # are preserved in each search log; the saved HTML shell alone is not evidence.
    qualified={}; discovery=[]
    for f in sorted((ROOT/'data/raw/candidate_discovery').glob('search_*.json')):
        for item in json.loads(f.read_text()):
            discovery.append(dict(candidate_key=item['candidate_key'],candidate_name=item['candidate_name'],query=item['query'],source_file=str(f.relative_to(ROOT)),status='searched' if item.get('result') else 'search_failed'))
            for block in item.get('result','').split('--------------------------------------------------------------------------------'):
                if '('+QUAL+')' not in block:continue
                for county,count,names in re.findall(r'（[一二三四五六七八九十]+）([^：。\s]+?[市縣])(\d+)人：([^。\n]+)',block):
                    for name in names.split('、'):
                        qualified[(county,name)]=str(f.relative_to(ROOT))
    for r in base.itertuples():
        if (r.county_city,r.candidate_name) in qualified:
            observe(r.candidate_name,'qualification_status','approved_2026-10-16','official_announcement_indexed_excerpt',QUAL,qualified[(r.county_city,r.candidate_name)],'審查通過名單 '+r.county_city,'2026-10-16','official_page_excerpt_via_search_index')

    # All-office archive: preserve every name hit, including rejected namesakes.
    history=[]
    manifest=json.loads((ROOT/'data/raw/cec_all_offices_manifest.json').read_text())
    for item in manifest['members']:
        member=item['archive_member']; after=member.split('/voteData/',1)[-1]
        yearmatch=re.search(r'(?<!\d)(19\d{2}|20\d{2})',after)
        year=yearmatch[1] if yearmatch else {'3屆立委':'1995','4屆立委':'1998','5屆立委':'2001','9任總統':'1996'}.get(after.split('/')[0],'')
        for lineno,row in enumerate(csv.reader(io.StringIO((ROOT/item['path']).read_text(encoding='utf-8-sig'))),1):
            if len(row)<14:continue
            name=row[6].strip()
            if name not in byname:continue
            born=iso_roc(row[9]); sex={'1':'男','2':'女'}.get(row[8].strip().lstrip("'"),'')
            # C1 is county/metropolitan chief in the 2022 archive, not township.
            mayor=('/C1/' in after or after.split('/')[-2] in ['1994直轄市長','1997縣市長','1998直轄市長','2001縣市長','2002直轄市長','2005縣市長','2006直轄市長','縣市長','市長','直轄市市長','縣市市長'])
            fields=media.get(name,{})
            media_born=next((iso_media(value) for label,value in fields.items() if label in ['生日','出生'] and iso_media(value)),'')
            primary_born=next((b for n,b,_,_ in pdfclaims if n==name),'')
            compare=primary_born or media_born
            status='dob_corroborated_by_official_bulletin' if primary_born and born==primary_born else 'dob_corroborated_by_media' if compare and born==compare else 'rejected_birth_date_mismatch' if compare and born and born!=compare else 'name_only_pending_identity'
            history.append(dict(candidate_key=byname[name],candidate_name=name,election_year=year,election_context=after,office_is_county_city_mayor='1' if mayor else '0',sex=sex,birth_date=born,birth_raw=row[9],education_level_cec=row[12].strip(),geography_codes='|'.join(x.lstrip("'") for x in row[:5]),elected_marker=row[14].strip() if len(row)>14 else '',source_file=item['path'],source_row=str(lineno),source_archive_member=member,source_url=CEC,identity_match_status=status))
    hist=pd.DataFrame(history).fillna('')
    # Follow-up on the 25 previously missing values. Community claims stay separate.
    sex_evidence=read_csv(ROOT/'data/raw/sex_verification/sex_evidence.csv')
    for claim in sex_evidence.itertuples():
        assert claim.candidate_key==byname[claim.candidate_name]
        assert claim.sex_value in ['男','女']
        field='sex_directory_supplement' if claim.source_type=='community_directory_sex' else 'sex'
        observe(claim.candidate_name,field,claim.sex_value,claim.source_type,claim.source_url,claim.source_file,claim.source_locator,claim.source_time_context,claim.verification_status)
    userfile='data/raw/sex_verification/user_sex_updates_20261017.csv'
    user_sex=read_csv(ROOT/userfile)
    for claim in user_sex.itertuples():
        assert claim.candidate_key==byname[claim.candidate_name]
        assert claim.reported_sex in ['男','女','未知']
        observe(claim.candidate_name,'sex_reported_unknown' if claim.reported_sex=='未知' else 'sex',claim.reported_sex,'user_provided','',userfile,'User message; candidate name and county matched','2026-10-17','user_reported_unknown' if claim.reported_sex=='未知' else 'user_provided_not_independently_verified')
    # GVM is a media compilation: compare roster/party first, retain education claims as such.
    gvmfile='data/raw/gvm_20261017/election-2026.json'
    gvm=json.loads((ROOT/gvmfile).read_text()); gvm_education={}; gvm_keys=[]
    party_alias={'國民黨':'中國國民黨','民進黨':'民主進步黨','民眾黨':'台灣民眾黨','台聯':'台聯黨','無黨籍':'無黨籍及未經政黨推薦'}
    for city in gvm['cities']:
        for person in city['candidates']:
            # Explicit 温/溫 name variant; no fuzzy person matching.
            name='温世政' if person['name']=='溫世政' else person['name']
            matched=base.loc[(base.candidate_name==name)&(base.county_city.map(norm)==norm(city['name']))]
            assert len(matched)==1,(city['name'],name)
            candidate=matched.iloc[0];gvm_keys.append(candidate.candidate_key)
            assert norm(party_alias.get(person['partyName'],person['partyName']))==norm(candidate.party_at_registration),(name,person['partyName'])
            education=[x for x in person.get('education',[]) if x.strip() and x.strip() not in ['尚未公布','待補','未知']]
            if education:
                value='；'.join(education);gvm_education[name]=value
                observe(name,'education_gvm_compilation',value,'media_supplement','https://event.gvm.com.tw/2026_rank/?city='+city['slug'],gvmfile,'cities[id='+city['id']+'].candidates[id='+person['id']+'].education','captured 2026-10-17','media_compilation_roster_party_matched_degrees_not_independently_verified')
    assert len(gvm_keys)==81 and len(set(gvm_keys))==81 and set(gvm_keys)==set(base.candidate_key)
    obs=pd.DataFrame(observations).drop_duplicates().reset_index(drop=True)
    camp=pd.DataFrame(campaigns).drop_duplicates(['candidate_key','source_kind','url']).reset_index(drop=True)
    blocks=pd.DataFrame(texts).drop_duplicates(['candidate_key','source_url','text_original']).reset_index(drop=True)
    enriched=base.copy()
    extra=['birth_date_source_url','birth_date_evidence_status','sex_source_url','education_profile_as_captured','education_profile_source_url','education_media_supplement','education_latest_cec','education_latest_cec_year','media_birth_original','media_birth_year','birth_date_media_supplement','age_2026_from_media_birth_year','media_experience_supplement','official_profile_url','official_campaign_website','official_facebook_url','official_facebook_link_evidence','qualification_source_url','prior_any_office_evidence_url','prior_mayor_evidence_file','first_time_any_evidence_status','first_time_mayor_evidence_status','no_prior_mayor_match_in_available_archive','identity_conflict_notes','background_collection_status']
    extra+=['sex_source_tier','sex_evidence_status','sex_directory_supplement','sex_directory_source_url']
    for c in extra:enriched[c]=''
    def pick(rows,field):
        sub=rows.loc[rows.field==field]
        return sub.iloc[0] if len(sub) else None
    for i,r in enriched.iterrows():
        key=r.candidate_key; name=r.candidate_name; own=obs.loc[obs.candidate_key==key]
        fh=hist.loc[hist.candidate_key==key]
        accepted=fh.loc[fh.identity_match_status.str.startswith('dob_corroborated')].sort_values(['election_year','source_file'])
        primary=own.loc[own.source_type!='media_supplement']
        sx=pick(primary,'sex'); bd=pick(primary,'birth_date'); edu=pick(primary,'education_profile'); inc=pick(primary,'incumbency'); qual=pick(primary,'qualification_status')
        if sx is not None:
            enriched.loc[i,['sex_2026','sex_source_url','sex_source_tier','sex_evidence_status']]=[sx.value,sx.source_url,sx.source_type,sx.verification_status]
        directory=pick(own,'sex_directory_supplement')
        unknown=pick(own,'sex_reported_unknown')
        if sx is None and unknown is not None:
            enriched.loc[i,['sex_source_tier','sex_evidence_status']]=['user_provided','user_reported_unknown']
        if directory is not None:
            enriched.loc[i,['sex_directory_supplement','sex_directory_source_url']]=[directory.value,directory.source_url]
        if bd is not None:enriched.loc[i,['birth_date_verified','birth_date_source_url','birth_date_evidence_status']]=[bd.value,bd.source_url,bd.verification_status]
        if len(accepted):
            latest=accepted.iloc[-1]
            if sx is None:enriched.loc[i,['sex_2026','sex_source_url','sex_source_tier','sex_evidence_status']]=[latest.sex,CEC,'historical_CEC',latest.identity_match_status]
            if bd is None and latest.birth_date:enriched.loc[i,['birth_date_verified','birth_date_source_url','birth_date_evidence_status']]=[latest.birth_date,CEC,'CEC_name_and_birth_date_corroborated_by_CNA']
            enriched.loc[i,['education_latest_cec','education_latest_cec_year']]=[latest.education_level_cec,latest.election_year]
            enriched.loc[i,['first_time_any_elected_office','prior_any_office_evidence_url','first_time_any_evidence_status']]=['0',CEC,'prior_CEC_record_name_and_birth_date_corroborated']
            may=accepted.loc[accepted.office_is_county_city_mayor=='1']
            if len(may):enriched.loc[i,['first_time_mayor_lifetime','prior_mayor_evidence_file','first_time_mayor_evidence_status']]=['0',may.iloc[-1].source_file,'prior_CEC_mayoral_record_name_and_birth_date_corroborated']
            enriched.loc[i,'history_identity_verified']='name_plus_birth_date_corroborated; see source tier'
        prior=pick(primary,'prior_elected_office')
        if prior is not None:enriched.loc[i,['first_time_any_elected_office','prior_any_office_evidence_url','first_time_any_evidence_status']]=['0',prior.source_url,'positive_prior_elected_office_evidence']
        if edu is not None:enriched.loc[i,['education_profile_as_captured','education_profile_source_url']]=[edu.value,edu.source_url]
        if inc is not None:enriched.loc[i,'incumbency_2026']=inc.value
        if qual is not None:enriched.loc[i,['qualification_status','qualification_source_url']]=[qual.value,qual.source_url]
        m=media.get(name,{})
        enriched.loc[i,'education_media_supplement']=m.get('學歷','')
        if not m.get('學歷','') and name in gvm_education:
            enriched.loc[i,'education_media_supplement']='[遠見補充；學位待核實] '+gvm_education[name]
        enriched.loc[i,'media_experience_supplement']=m.get('經歷','')
        born_raw=next((v for k,v in m.items() if k in ['生日','出生','出生年','生日年月']),'')
        enriched.loc[i,'media_birth_original']=born_raw
        enriched.loc[i,'birth_date_media_supplement']=iso_media(born_raw)
        y=re.search(r'(\d{4})年',born_raw)
        if y:
            enriched.loc[i,'media_birth_year']=y[1]
            enriched.loc[i,'age_2026_from_media_birth_year']=str(2026-int(y[1]))
        if enriched.loc[i,'birth_date_verified']:
            enriched.loc[i,'age_2026_minus_birth_year']=str(2026-int(enriched.loc[i,'birth_date_verified'][:4]))
        if born_raw and not iso_media(born_raw):
            issues.append(dict(candidate_key=key,candidate_name=name,field='media_birth_original',issue='Partial or malformed source date retained, no invented full date',source_file=cnafile))
        conflicts=fh.loc[fh.identity_match_status=='rejected_birth_date_mismatch']
        if len(conflicts):enriched.loc[i,'identity_conflict_notes']=str(len(conflicts))+' historical namesake/date conflicts excluded; inspect all-office history'
        enriched.loc[i,'no_prior_mayor_match_in_available_archive']='0' if len(accepted.loc[accepted.office_is_county_city_mayor=='1']) else '1'
        links=camp.loc[camp.candidate_key==key]
        for kind,column in [('official_profile','official_profile_url'),('candidate_website','official_campaign_website'),('facebook.com','official_facebook_url')]:
            selected=links.loc[links.source_kind==kind]
            if len(selected):enriched.loc[i,column]=selected.iloc[0].url
        fb=links.loc[links.source_kind=='facebook.com']
        if len(fb):enriched.loc[i,'official_facebook_link_evidence']=fb.iloc[0].discovered_on
        enriched.loc[i,'first_time_review_status']='positive_history_recorded; first-ever claims remain pending' if enriched.loc[i,'first_time_any_elected_office']=='0' else 'pending_lifetime_history'
        enriched.loc[i,'background_collection_status']='partial_with_sources' if len(own) else 'searched_no_verified_background'
    # Keep the ambiguous education_2026 field blank: source-specific education is above.
    coverage=[]
    for r in enriched.itertuples():
        own=obs.loc[obs.candidate_key==r.candidate_key]; links=camp.loc[camp.candidate_key==r.candidate_key]
        coverage.append(dict(candidate_key=r.candidate_key,county_city=r.county_city,candidate_name=r.candidate_name,qualification_status=r.qualification_status,sex_available=int(bool(r.sex_2026)),primary_birth_date_available=int(bool(r.birth_date_verified)),media_birth_year_available=int(bool(r.media_birth_year)),primary_profile_education_available=int(bool(r.education_profile_as_captured)),historical_cec_education_available=int(bool(r.education_latest_cec)),media_education_available=int(bool(r.education_media_supplement)),first_time_mayor_resolved=int(bool(r.first_time_mayor_lifetime)),first_time_any_office_resolved=int(bool(r.first_time_any_elected_office)),official_facebook_link_found=int(bool(r.official_facebook_url)),campaign_website_found=int(bool(r.official_campaign_website)),campaign_text_blocks=int((blocks.candidate_key==r.candidate_key).sum()),source_search_attempted=1,facebook_posts_collected=0,window_post_count_status='not_collected_not_zero',remaining=';'.join(k for k in ['birth_date_verified','education_profile_as_captured','incumbency_2026','first_time_mayor_lifetime','first_time_any_elected_office','official_facebook_url'] if not getattr(r,k))))
    outputs={'candidates_2026_enriched':enriched,'candidate_profile_observations':obs,'candidate_all_office_history':hist,'candidate_campaign_sources':camp,'candidate_campaign_text_blocks':blocks,'candidate_collection_coverage':pd.DataFrame(coverage),'candidate_source_search_log':pd.DataFrame(discovery),'candidate_source_issues':pd.DataFrame(issues)}
    verification={}
    for key,frame in outputs.items():
        assert frame.columns.is_unique and not frame.duplicated().any(),key
        assert set(frame.candidate_key)<=set(base.candidate_key),key
        path=ROOT/'data/processed'/f'{key}.csv'
        frame.to_csv(path,index=False,encoding='utf-8-sig')
        saved=read_csv(path)
        pd.testing.assert_frame_equal(frame.fillna('').astype(str).reset_index(drop=True),saved,check_dtype=False)
        verification[key]={'path':str(path.relative_to(ROOT)),'rows':len(saved),'columns':list(saved.columns),'sha256':digest(path)}
    assert len(enriched)==81 and enriched.candidate_key.is_unique
    assert (enriched.first_time_mayor_lifetime!='1').all() and (enriched.first_time_any_elected_office!='1').all()
    assert enriched.loc[enriched.candidate_name=='李四川','first_time_any_elected_office'].iloc[0]=='', 'Exclude unrelated village-chief namesake'
    assert not (hist.loc[hist.identity_match_status=='rejected_birth_date_mismatch'].index.intersection(hist.loc[hist.identity_match_status.str.startswith('dob_corroborated')].index)).size
    for relative,expected in expected_inputs.items():assert digest(ROOT/relative)==expected
    return outputs,verification
