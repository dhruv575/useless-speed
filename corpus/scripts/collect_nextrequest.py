"""Collect public signal records using an isolated, headless Chrome context.

Public endpoints were observed in the site's own browser UI. No authentication,
unpublished records, or state-changing request endpoints are used.
"""
import argparse, asyncio, hashlib, json, re, sys
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE='https://sanfrancisco.nextrequest.com'
META=ROOT/'metadata'; RAW=ROOT/'raw'/'nextrequest'
for folder in (META/'searches',META/'requests',RAW): folder.mkdir(parents=True,exist_ok=True)

def save(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def slug(text): return re.sub(r'[^a-zA-Z0-9._-]+','_',text).strip('_')[:145]

def classify(doc):
    name=doc['title']; t=name.lower(); ext=doc.get('file_extension','').lower()
    if ext in ('syn','sim','utdf','trf','dqt','sig','vissim','inpx','inp'): return 'traffic_model'
    if re.search(r'(?:^|[ _])ch(?:ange)?[ _]*\d+|timing|phasing|signal.*(?:plan|schedule)|(?:plan|schedule).*signal',t):
        if re.match(r'^(re|fw|fwd)[ _:]',t): return 'technical_correspondence'
        return 'timing_or_signal_plan'
    if re.search(r'synchro|signal.*(?:drawing|installation)|(?:sid|cp)[ _.-]|\bsid\b',t): return 'signal_design'
    if re.search(r'(traffic|intersection|turning|volume|pedestrian).*(count|stud|analys)|(?:count|stud|analys).*traffic|\b(am|pm)[ _].*\d{4}',t): return 'traffic_study_or_counts'
    if re.search(r'signal|greenwave|green wave|retiming|coordination|\bsrc\b',t): return 'signal_related'
    return 'other'

async def get_json(context,path,params=None):
    url=BASE+path+('?' + urlencode(params) if params else '')
    for attempt in range(4):
        response=await context.request.get(url,timeout=60000)
        if response.status==429 or response.status>=500:
            await asyncio.sleep(2**attempt); continue
        if response.status!=200: raise RuntimeError(f'{response.status} {url}')
        data=await response.json()
        if 'message' in data and len(data)<3: raise RuntimeError(str(data))
        return data,url
    raise RuntimeError('Retries exceeded '+url)

async def discover(context):
    catalog={}; requests={}; searches=[]
    queries=['timing','signal','synchro','phasing','green wave','offset','traffic study','traffic counts','.syn','.sim']
    for query in queries:
        page=1; gathered=[]
        while True:
            params={'search_term':query,'sort_field':'count','sort_order':'desc','page_size':50,'page_number':page}
            data,url=await get_json(context,'/client/documents',params)
            docs=data.get('documents',[]); gathered.extend(docs)
            for d in docs:
                d={**d,'source_url':BASE+d['document_path'],'search_terms':[query]}
                if str(d['id']) in catalog:
                    catalog[str(d['id'])]['search_terms'].append(query)
                else: catalog[str(d['id'])]=d
            if len(gathered)>=data.get('total_count',0) or not docs: break
            page+=1
            if page>200: raise RuntimeError('Unexpected large query '+query)
        save(META/'searches'/f'documents_{slug(query)}.json',{'query':query,'total':data['total_count'],'documents':gathered})
        searches.append({'query':query,'kind':'documents','total':data['total_count'],'collected':len(gathered)})
        print('SEARCH',query,data['total_count'],'unique',len(catalog),flush=True)
    for query in ['signal','timing','synchro']:
        page=1; seen=set(); gathered=[]
        while True:
            data,url=await get_json(context,'/client/requests',{'search_term':query,'page_number':page})
            rows=data.get('requests',[])
            new=[r for r in rows if str(r['id']) not in seen]
            if not new: break
            for r in new: seen.add(str(r['id'])); requests[str(r['id'])]=r
            gathered.extend(new)
            if len(seen)>=data['total_count']: break
            page+=1
        searches.append({'query':query,'kind':'requests','total':data['total_count'],'collected':len(gathered)})
        save(META/'searches'/f'requests_{slug(query)}.json',{'query':query,'total':data['total_count'],'requests':gathered})
        print('REQUEST SEARCH',query,data['total_count'],len(gathered),flush=True)
    # Follow requests likely to contain actual timings, plans or models, and all
    # requests with strong document hits. Procurement-only requests are excluded.
    selected={'25-2143','22-3290'}
    for r in requests.values():
        t=r.get('request_text','').lower()
        if re.search(r'traffic signal|signal tim|timing (?:card|plan)|synchro|signal phas',t) and not re.search(r'certified payroll|bid tabulation|subcontractor|sub-contractor|award notice|bid packet|insurance|payment bond',t): selected.add(str(r['id']))
    for d in catalog.values():
        if classify(d) in ['timing_or_signal_plan','traffic_model','signal_design','traffic_study_or_counts'] and d.get('pretty_id'):
            if not re.search(r'recology|fund timing|payment timing|rate timing|noticing|payment schedule',d['title'],re.I): selected.add(d['pretty_id'])
    save(META/'request_candidates.json',list(requests.values()))
    for rid in sorted(selected):
        page=1; gathered=[]; seen=set()
        while True:
            params={'request_id':rid,'page_number':page,'visibility':'all','folderless_docs':'false','sort_field':'id','sort_order':'asc'}
            try: data,url=await get_json(context,'/client/request_documents',params)
            except Exception as e: print('REQUEST ERROR',rid,str(e),flush=True); break
            docs=data.get('documents',[]); new=[d for d in docs if str(d['id']) not in seen]
            if not new: break
            for d in new:
                seen.add(str(d['id'])); gathered.append(d)
                if d.get('visibility','').lower()!='public': continue
                key=str(d['id']); old=catalog.get(key,{})
                catalog[key]={**old,**d,'pretty_id':rid,'source_url':BASE+'/documents/'+key,'search_terms':old.get('search_terms',[]),'expanded_request':True}
            if len(gathered)>=data.get('current_documents_count',0): break
            page+=1
        if gathered:
            save(META/'requests'/f'{rid}_documents.json',gathered)
        print('REQUEST',rid,len(gathered),'unique',len(catalog),flush=True)
    for d in catalog.values():
        d['category']=classify(d)
        d['proposed_or_draft_in_title']=bool(re.search('propos|draft|concept|future',d['title'],re.I))
    save(META/'catalog.json',list(catalog.values()))
    save(META/'search_log.json',searches)
    print('DISCOVERY COMPLETE',len(catalog),len(selected),flush=True)

async def download(context):
    docs=json.loads((META/'catalog.json').read_text(encoding='utf-8'))
    manifest_path=META/'downloads.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    selected=[]
    for d in docs:
        t=d['title'].lower(); ext=d.get('file_extension','').lower()
        if re.search(r'recology|fund timing|payment timing|rate timing|noticing|col[a ]|pier 96|hazardous|sfpd|bid tabulation|certified payroll|traffic citation|signal app',t): continue
        category=d['category']
        if category=='other':
            # Complete engineering attachments within signal-specific requests,
            # but not the unrelated correspondence/photo collections.
            if not (d.get('expanded_request') and ext in ['xls','xlsx','syn','sim','zip']): continue
        if ext not in ['pdf','xls','xlsx','csv','txt','syn','sim','utdf','trf','dqt','sig','inpx','inp','zip','dwg','html','htm']: continue
        selected.append(d)
    save(META/'download_selection.json',selected)
    sem=asyncio.Semaphore(3)
    async def one(d):
        async with sem:
            key=str(d['id'])
            if manifest.get(key,{}).get('status')=='ok' and (ROOT/manifest[key]['local_path']).exists(): return
            filename=key+'__'+slug(d['title'])
            suffix='.'+d.get('file_extension','')
            if not filename.lower().endswith(suffix.lower()): filename+=suffix
            target=RAW/filename
            row={'id':key,'title':d['title'],'request_id':d.get('pretty_id'),'source_url':d['source_url'],'category':d['category'],'retrieved_at':datetime.now(timezone.utc).isoformat()}
            try:
                response=await context.request.get(BASE+f'/documents/{key}/download?token=',timeout=90000)
                body=await response.body(); ct=response.headers.get('content-type','')
                if response.status!=200 or (len(body)<50000 and b'<html' in body[:300].lower() and d.get('file_extension') not in ['htm','html']): raise RuntimeError(f'HTTP {response.status}; {ct}; {len(body)} bytes')
                if d.get('file_extension')=='pdf' and not body.startswith(b'%PDF'): raise RuntimeError('Invalid PDF signature')
                target.write_bytes(body)
                row.update(status='ok',local_path=str(target.relative_to(ROOT)).replace('\\','/'),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),content_type=ct)
                await response.dispose()
                print('SAVED',key,len(body),d['title'],flush=True)
            except Exception as e:
                row.update(status='error',error=str(e)); print('FAILED',key,str(e),flush=True)
            manifest[key]=row; save(manifest_path,manifest)
    print('DOWNLOAD SELECTION',len(selected),flush=True)
    await asyncio.gather(*(one(d) for d in selected))

async def main():
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['discover','download','all']); args=parser.parse_args()
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context()
        page=await context.new_page()
        await page.goto(BASE+'/documents')
        await page.get_by_role('textbox',name='Type here to filter by document name').wait_for()
        save(META/'collection_environment.json',{'headless':True,'user_agent':await page.evaluate('navigator.userAgent'),'started_at':datetime.now(timezone.utc).isoformat(),'source':BASE,'authentication':'none'})
        if args.mode in ['discover','all']: await discover(context)
        if args.mode in ['download','all']: await download(context)
        await browser.close()

if __name__=='__main__': asyncio.run(main())
