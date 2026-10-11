"""Archive the public data requests exposed by SFCTA's dashboards."""
import asyncio,json,hashlib,re,sys
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
ROOT=Path(__file__).resolve().parents[1];META=ROOT/'metadata';RAW=ROOT/'raw'/'sfcta';RAW.mkdir(parents=True,exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
async def main():
 urls={}
 for name in ['cmp','congestion']:
  for e in json.loads((META/'dashboard_network'/f'{name}_network.json').read_text(encoding='utf-8')):
   u=e['url']
   if 'api.sfcta.org/api/' not in u or u.endswith('select=year') or u.endswith('select=date'):continue
   table=u.split('/api/')[-1].split('?')[0]
   if table=='inrix_rt_hourly_exp':u=u.split('?')[0]+'?select=cmp_segid,date,period,avg_speed'
   urls[table]=u
 manifest={};mp=META/'speed_downloads.json'
 if mp.exists():manifest=json.loads(mp.read_text(encoding='utf-8'))
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True);c=await b.new_context()
  for table,url in urls.items():
   if manifest.get(table,{}).get('status')=='ok':continue
   row={'id':'sfcta_'+table,'title':'SFCTA '+table,'source_url':url,'discovery_url':'https://congestion.sfcta.org' if table.startswith('inrix') else 'https://cmp.sfcta.org','category':'observed_speeds' if not 'segments' in table else 'road_geometry','retrieved_at':datetime.now(timezone.utc).isoformat()}
   try:
    response=await c.request.get(url,headers={'Prefer':'count=exact'},timeout=180000)
    if response.status!=200:raise RuntimeError(f'HTTP {response.status}')
    body=await response.body();data=json.loads(body)
    if not isinstance(data,list):raise RuntimeError(str(data)[:300])
    target=RAW/(table+'.json');target.write_bytes(body)
    span={}
    for field in ['year','date']:
     vals=[r[field] for r in data if r.get(field) is not None]
     if vals:span[field+'_min']=min(vals);span[field+'_max']=max(vals)
    content_range=response.headers.get('content-range')
    row.update(status='ok',local_path=target.relative_to(ROOT).as_posix(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),row_count=len(data),fields=list(data[0]) if data else [],content_range=content_range,**span)
    await response.dispose();print('SAVED',table,len(data),len(body),span,content_range,flush=True)
   except Exception as e:row.update(status='error',error=str(e));print('ERROR',table,str(e),flush=True)
   manifest[table]=row;save(mp,manifest)
  await b.close()
if __name__=='__main__':asyncio.run(main())
