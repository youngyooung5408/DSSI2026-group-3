"""Executed by the companion notebook; source-reported sex, never inferred."""
from pathlib import Path
from collections import Counter
import csv, json, hashlib, copy
from bs4 import BeautifulSoup
from sex_focus_helpers_20261103 import *
DATE='2026-11-03'
SNAP='data/processed/snapshots/pre_sex_focus_20261103/'

def write_csv(root,path,rows):
    target=(root/path).resolve()
    assert target.is_relative_to((root/'data/processed').resolve())
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    assert read_csv(root,path)==rows, path

def run(root):
    root=Path(root)
    pins=json.loads((root/'data/code/sex_focus_inputs_20261103.json').read_text())
    for path,digest in pins.items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest, ('input changed',path)
    regs=read_csv(root,'data/processed/council_candidates_2026_registration.csv')
    fields=read_csv(root,SNAP+'candidate_fields_current.csv')
    master=read_csv(root,SNAP+'candidate_master_current.csv')
    bg=read_csv(root,SNAP+'council_background_20261019.csv')
    before=copy.deepcopy((fields,master,bg))
    keys={r['candidate_key'] for r in regs}
    assert len(keys)==len(regs)==1502
    sf={x['candidate_key']:x for x in fields if x['field']=='sex' and x['candidate_key'] in keys}
    mi={x['candidate_key']:x for x in master}; bi={x['candidate_key']:x for x in bg}
    assert len(sf)==len(bi)==1502
    latest=extract_wiki(root,RAW+'wiki_1.source',WIKI_URL,'captured_2026-11-03')
    old=extract_wiki(root,RAW+'wiki_old_rendered.json','https://zh.wikipedia.org/w/index.php?oldid=94459742','revision_94459742_2026-09-20')
    assert (len(latest),len(old))==(1493,1499)
    li,oi=index_wiki(latest),index_wiki(old)
    history,_=historical_council_index(root)
    reviews=json.loads((root/'data/code/sex_focus_name_review_20261103.json').read_text())
    rev={(norm(x['county_city']),x['district_number'],x['candidate_name']):x for x in reviews}
    # Validate every manually reviewed spelling against the preserved national ballot table.
    soup=BeautifulSoup((root/RAW/'yunlin_ballot.html').read_bytes(),'html.parser')
    for x in reviews:
        detail=[d for d in soup.select('details.council') if norm(d.select_one('.council-name').get_text(strip=True))==norm(x['county_city'])]
        assert len(detail)==1
        dt=[d for d in detail[0].find_all('dt') if district_number(d.get_text())==x['district_number']]
        assert len(dt)==1
        candidates=[e for e in dt[0].find_next_sibling('dd').select('.nm') if e.find('a') and e.find('a').get_text(strip=True)==x['candidate_name']]
        assert len(candidates)==1 and candidates[0].find('small').get_text(strip=True).split()[0]==x['ballot_number'],x
    direct={
        ('嘉義縣','魏彰儀'):('男','chiayi_registration_sex.html','https://www.tcpttw.com/other/other_local/2026/09/04/307178/','魏彰儀（男、無黨籍）'),
        ('嘉義縣','何博倫'):('男','chiayi_registration_sex.html','https://www.tcpttw.com/other/other_local/2026/09/04/307178/','何博倫(男、無黨籍)'),
        ('雲林縣','鄭玫惠'):('女','yunlin_registration_sex.html','https://seenews.tw/105634','鄭玫惠（女，無）'),
    }
    for sex,file,url,quote in direct.values():assert quote in body(root,RAW+file)
    result=[];conflicts=[]
    for r in regs:
        key=r['candidate_key'];f=sf[key];previous=f['existing_value'];b=bi[key]
        a=match_wiki(r,li);o=match_wiki(r,oi);review=rev.get((norm(r['county_city']),district_number(r['electoral_district']),r['candidate_name']))
        method='same_county_district_unique_normalized_chinese_name'
        if review:
            assert a is None
            a=match_wiki(r,li,review['source_name']);assert a and a['ballot_number']==review['ballot_number']
            method='reviewed_spelling_same_county_district_ballot'
        observation=a or o
        hs=history[(norm(r['county_city']),district_number(r['electoral_district']),chinese_name(r['candidate_name']))]
        h=hs[0] if len(hs)==1 else None
        if previous:
            value=previous;tier='prior_record_retained';url=f['evidence'];file=SNAP+'candidate_fields_current.csv';locator=key+'; field=sex';year='see_prior_evidence';source_name=r['candidate_name'];method='prior_evidence_preserved'
        else:
            assert observation,('missing evidence',r)
            value=observation['sex'];tier='secondary_2026_explicit_sex';url=observation['source_url'];file=observation['source_file'];locator=observation['source_locator'];year='2026';source_name=observation['source_name']
        issue=[]
        if a and o and a['sex']!=o['sex']:
            issue.append('wiki_revision_disagreement')
            conflicts.append(dict(candidate_key=key,candidate_name=r['candidate_name'],issue='wiki_revision_disagreement',source_a=a['source_url'],value_a=a['sex'],source_b=o['source_url'],value_b=o['sex'],resolution='保留既有值或最新明載值；歷史版本差異另列，不視為獨立查證'))
        if not previous and (norm(r['county_city']),r['candidate_name']) in direct:
            value,file0,url,quote=direct[(norm(r['county_city']),r['candidate_name'])]
            tier='media_2026_registration_explicit_sex';file=RAW+file0;locator=quote;source_name=r['candidate_name'];year='2026'
        unresolved='0'
        if not previous and h and observation and h['sex']!=observation['sex']:
            assert r['candidate_name']=='張光儀'
            # Retain an explicitly dated official historical value, with a blocking current-data flag.
            value=h['sex'];tier='official_2022_historical_current_conflict';url='https://db.cec.gov.tw/';file=h['source_file'];locator='CSV row '+h['source_row'];year='2022';source_name=h['source_name'];unresolved='1'
            issue.append('official_2022_vs_secondary_2026_unresolved')
            conflicts.append(dict(candidate_key=key,candidate_name=r['candidate_name'],issue=issue[-1],source_a=h['source_file']+':'+h['source_row'],value_a=h['sex'],source_b=observation['source_url'],value_b=observation['sex'],resolution='僅收錄2022官方申報值；2026衝突未裁定，exclude_from_unqualified_2026_analysis=1'))
        if r['candidate_name']=='陳泱瑚' and norm(r['county_city'])=='金門縣':
            alt=match_wiki(r,li,'陳映瑚');assert alt and alt['ballot_number']=='17' and previous=='男' and alt['sex']=='女'
            issue.append('secondary_name_and_sex_disagree_with_prior_official')
            conflicts.append(dict(candidate_key=key,candidate_name=r['candidate_name'],issue=issue[-1],source_a=f['evidence'],value_a=previous,source_b=alt['source_url'],value_b=alt['sex'],resolution='保留既有官方歷史值；維基同號次姓名及性別均不同，不覆寫；需當屆官方複核'))
        if r['candidate_name']=='王珍玨':
            assert '正妹選將王珍玨' in body(root,RAW+'wang_media.html')
            issue.append('latest_female_supported_by_media_gendered_description_not_official_field')
        note='; '.join(issue)
        corroboration=(h['source_file']+':'+h['source_row']) if h and h['sex']==value else ''
        result.append(dict(candidate_key=key,candidate_name=r['candidate_name'],county_city=r['county_city'],electoral_district=r['electoral_district'],sex=value,source_tier=tier,source_year=year,source_url=url,source_file=file,source_locator=locator,source_name=source_name,match_method=method,identity_review_source=review['identity_source_file'] if review else '',official_2022_same_name_district_agreement=corroboration,previous_value=previous,review_note=note,exclude_from_unqualified_2026_analysis=unresolved,checked_date=DATE))
        if not previous:
            status='2022官方性別有值；2026來源衝突待核' if unresolved=='1' else '2026次級來源明載；官方複核待補'
            f.update(existing_value=value,status=status,evidence=url+' | '+file+' | '+locator,note='source_tier='+tier+'; source_year='+year+'; '+method+'; '+note,next_source='2026官方選舉公報或候選人名冊性別欄複核',updated_date=DATE)
            mi[key].update(sex_status=status,updated_date=DATE)
            b.update(sex_additional_source_value=value,sex_additional_source_url=url,sex_additional_source_year=year,updated_date=DATE)
        b['sex_focus_source_tier']=tier;b['sex_focus_review_note']=note;b['sex_focus_current_conflict']=unresolved
    assert len(result)==1502 and all(x['sex'] in {'男','女'} for x in result)
    assert sum(bool(x['previous_value']) for x in result)==717
    assert sum(x['exclude_from_unqualified_2026_analysis']=='1' for x in result)==1
    assert len(conflicts)==6
    # Changes are limited to missing council sex and explicit review metadata.
    for oldrow,new in zip(before[0],fields):
        if oldrow['field']!='sex' or oldrow['candidate_key'] not in keys or oldrow['existing_value']:assert oldrow==new
    for oldrow,new in zip(before[1],master):
        assert {k:v for k,v in oldrow.items() if k not in {'sex_status','updated_date'}}=={k:v for k,v in new.items() if k not in {'sex_status','updated_date'}}
    allowed={'sex_additional_source_value','sex_additional_source_url','sex_additional_source_year','updated_date','sex_focus_source_tier','sex_focus_review_note','sex_focus_current_conflict'}
    for oldrow,new in zip(before[2],bg):assert {k:v for k,v in oldrow.items() if k not in allowed}=={k:v for k,v in new.items() if k not in allowed}
    outputs={'data/processed/candidate_fields_current.csv':fields,'data/processed/candidate_master_current.csv':master,'data/processed/council_background_20261019.csv':bg,'data/processed/council_sex_current.csv':result,'data/processed/council_sex_source_observations_20261103.csv':latest+old,'data/processed/council_sex_conflicts_20261103.csv':conflicts}
    verification={}
    for path,rows in outputs.items():
        write_csv(root,path,rows)
        verification[path]={'rows':len(rows),'columns':len(rows[0]),'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()}
    summary=dict(council_candidates=1502,previously_populated=717,newly_populated=785,populated=1502,current_source_conflict_unresolved=1,source_discrepancy_cases=len(conflicts),source_tiers=dict(Counter(x['source_tier'] for x in result)),outputs=verification)
    (root/'data/processed/council_sex_verification_20261103.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    assert json.loads((root/'data/processed/council_sex_verification_20261103.json').read_text())==summary
    return summary
