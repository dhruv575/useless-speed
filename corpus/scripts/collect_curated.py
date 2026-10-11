"""Build focused records corpus from public metadata previously discovered in UI."""
import asyncio, json, re
from collect_nextrequest import ROOT, META, BASE, save, slug, get_json, download
from playwright.async_api import async_playwright

NARROW=['25-2143','24-765','24-1053','25-1486','26-1203','24-6820','26-9464','25-131','25-16']

def category(d):
    t=d['title'].strip().lower(); ext=d.get('file_extension','').lower(); rid=d.get('pretty_id')
    if ext in ['syn','sim','utdf','trf','dqt','inpx','inp']: return 'traffic_model'
    if re.search(r'recology|fund timing|rate timing|payment timing|phasing|signage|dig.in|pullbox|punch list|bid|cost analysis|ncr|invoice|conduit|pole|calculation',t): return 'other'
    if rid=='25-2143':
        if re.search(r'ch[ _]*[01]|timing card',t) and not re.match(r'(re|fw)[_: ]',t): return 'timing_card'
        if re.search(r'timing|src|digisig',t): return 'timing_correspondence'
        if re.search(r'sid|\bcp\b',t): return 'signal_design'
        if re.search(r'2021|count|synchro',t): return 'traffic_study_or_counts'
    if re.match(r'(re|fw|fwd)[_: ]',t) or ext in ['html','htm','txt']: return 'other'
    if re.search(r'19th ave_sloat_.*timing',t): return 'timing_card'
    if re.search(r'signal',t) and ext in ['dwg','zip']: return 'signal_design'
    if re.search(r'signal',t) and ext=='pdf':
        if re.search(r'layout|drawing|asbuilt|as.built|design|progress set|signalphase|65%|75%|2652j-19th',t): return 'signal_design'
        if re.search(r'phase iii|psr.pr|allocation|arf',t): return 'signal_project_report'
    if re.search(r'traffic.*count|traffic.*stud|count.*traffic',t): return 'traffic_study_or_counts'
    if rid in NARROW and rid!='25-2143' and ext in ['pdf','xlsx','xls','dwg','zip'] and not re.search(r'claim|request|accident|collision|investigat|complaint|photos',t): return 'signal_request_attachment'
    return 'other'

async def main():
    catalog={}
    for f in (META/'searches').glob('documents_*.json'):
        s=json.loads(f.read_text(encoding='utf-8'))
        for d in s['documents']:
            key=str(d['id']); old=catalog.get(key,{})
            catalog[key]={**d,'source_url':BASE+d['document_path'],'search_terms':old.get('search_terms',[])+[s['query']]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context(); page=await context.new_page()
        await page.goto(BASE+'/documents')
        await page.get_by_role('textbox',name='Type here to filter by document name').wait_for()
        for rid in NARROW:
            cache=META/'requests'/f'{rid}_documents.json'; gathered=[]
            if cache.exists(): gathered=json.loads(cache.read_text(encoding='utf-8'))
            else:
                for suffix in ['', '/timeline']:
                    try:
                        data,_=await get_json(context,f'/client/requests/{rid}'+suffix)
                        save(META/'requests'/f'{rid}{"_timeline" if suffix else "_details"}.json',data)
                    except Exception as e: print('DETAIL ERROR',rid,str(e),flush=True)
                pn=1; seen=set()
                while True:
                    try:
                        data,_=await get_json(context,'/client/request_documents',{'request_id':rid,'page_number':pn,'visibility':'all','folderless_docs':'false','sort_field':'id','sort_order':'asc'})
                    except Exception as e: print('REQUEST ERROR',rid,str(e),flush=True);break
                    docs=[d for d in data.get('documents',[]) if str(d['id']) not in seen]
                    if not docs: break
                    gathered.extend(docs); seen.update(str(d['id']) for d in docs)
                    if len(gathered)>=data.get('current_documents_count',0):break
                    pn+=1; await asyncio.sleep(.3)
                save(cache,gathered)
            for d in gathered:
                if d.get('visibility','').lower()!='public':continue
                key=str(d['id']);old=catalog.get(key,{})
                catalog[key]={**old,**d,'pretty_id':rid,'source_url':BASE+'/documents/'+key,'search_terms':old.get('search_terms',[])}
            print('REQUEST',rid,len(gathered),flush=True)
        for d in catalog.values():
            d['category']=category(d)
            d['proposed_or_draft_in_title']=bool(re.search('propos|draft|concept|future|65%|75%',d['title'],re.I))
        save(META/'catalog.json',list(catalog.values()))
        print('SELECTED',sum(d['category']!='other' for d in catalog.values()),flush=True)
        await download(context)
        await browser.close()

if __name__=='__main__':asyncio.run(main())
