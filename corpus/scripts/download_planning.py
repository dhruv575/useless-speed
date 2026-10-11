"""Download published transportation and bundled technical appendices."""
import asyncio,json,re,hashlib,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
ROOT=Path(__file__).resolve().parents[1];META=ROOT/'metadata';RAW=ROOT/'raw'/'planning';RAW.mkdir(parents=True,exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def slug(s):return re.sub('[^a-zA-Z0-9._-]+','_',s)[:140].strip('_')
async def main():
 links={}
 for row in json.loads((META/'planning'/'projects.json').read_text(encoding='utf-8')):
  project=row['text'].split('\n')[0].split('\t')[0].strip()
  if re.search('Human Trafficking|District Attorney|SFO Recommended',project,re.I):continue
  for l in row['links']:
   t=l['title']
   if re.search(r'transport|\btraffic\b|synchro|travel demand|transit (?:assess|analys)',t,re.I): category='transportation_study'
   elif re.search(r'appendices|appendix',t,re.I) and re.search(r'Balboa Park Station|Treasure Island and Yerba|Central SoMa|Transit Center|Parkmerced|Geary Bus|Van Ness Bus',project,re.I):category='bundled_eir_appendices'
   elif re.fullmatch(r'(?i:(?:Draft (?:EIR|Environmental Impact Report)[ -]*)?Appendices)(?: [A-Z](?:[–-][A-Z])?)?',t):category='bundled_eir_appendices'
   else:continue
   if re.search(r'noise|cultural|water supply|shadow|air quality|wind|historic|notice|exemption',t,re.I) and not re.search(r'transport|traffic',t,re.I):continue
   links[l['url']]={**l,'project':project,'discovery_url':'https://sfplanning.org/environmental-review-documents','category':category}
 save(META/'planning'/'download_selection.json',list(links.values()))
 manpath=META/'planning_downloads.json';manifest=json.loads(manpath.read_text(encoding='utf-8')) if manpath.exists() else {}
 for r in manifest.values():r['selected_for_corpus']=r['source_url'] in links
 save(manpath,manifest)
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True);c=await b.new_context();sem=asyncio.Semaphore(3)
  async def one(l):
   async with sem:
    url=l['url'];key=hashlib.sha256(url.encode()).hexdigest()[:12]
    if manifest.get(key,{}).get('status')=='ok':return
    row={**l,'id':'planning_'+key,'title':l['project']+' — '+l['title'],'source_url':url,'selected_for_corpus':True,'retrieved_at':datetime.now(timezone.utc).isoformat()}
    try:
     target_url=url
     # These retired SF Planning hosts correspond to the department's public
     # S3 archive layout, also used by current links in this same library.
     parsed=urlparse(url)
     if parsed.hostname=='sfmea.sfplanning.org':target_url='https://sfplanning.s3.amazonaws.com/sfmea'+parsed.path
     elif parsed.hostname=='archives.sfplanning.org':target_url='https://sfplanning.s3.amazonaws.com/archives'+parsed.path
     elif parsed.hostname=='default.sfplanning.org' and parsed.path.startswith('/MEA/'):
      target_url='https://sfplanning.s3.amazonaws.com/sfmea/'+parsed.path.split('/')[-1]
     if target_url!=url:row['archive_url_resolution']='retired host mapped to public SF Planning S3 archive; verified by successful PDF response'
     r=await c.request.get(target_url,timeout=240000)
     if r.status!=200:raise RuntimeError(f'HTTP {r.status}')
     ct=r.headers.get('content-type','');body=await r.body();resolved=r.url
     if 'html' in ct:
      html=body.decode('utf-8',errors='replace');m=re.search(r"var RESTURI = '([^']+)'",html)
      if not m:raise RuntimeError('HTML has no public download link')
      resolved=urljoin(r.url,m[1]);await r.dispose()
      r=await c.request.get(resolved,timeout=180000)
      if r.status!=200:raise RuntimeError(f'HTTP {r.status} download')
      ct=r.headers.get('content-type','');body=await r.body()
     if not body.startswith(b'%PDF'):raise RuntimeError(f'Expected PDF, got {ct}, {len(body)} bytes')
     target=RAW/(key+'__'+slug(l['project'])+'__'+slug(l['title'])[:65]+'.pdf')
     # Keep the entire Windows path below legacy MAX_PATH for PDF tooling.
     if len(str(target))>245:target=RAW/(key+'__'+slug(l['project'])[:115]+'.pdf')
     target.write_bytes(body);await r.dispose()
     row.update(status='ok',local_path=target.relative_to(ROOT).as_posix(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),resolved_download_url=resolved,content_type=ct)
     print('SAVED',len(body),row['title'],flush=True)
    except Exception as e:row.update(status='error',error=str(e));print('ERROR',row['title'],str(e),flush=True)
    manifest[key]=row;save(manpath,manifest)
  print('SELECTED',len(links),flush=True)
  await asyncio.gather(*(one(l) for l in links.values()))
  await b.close()
if __name__=='__main__':asyncio.run(main())
