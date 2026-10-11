import asyncio,json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'raw'/'supporting';RAW.mkdir(parents=True,exist_ok=True)
META=ROOT/'metadata';MAN=META/'supporting_downloads.json'
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def slug(s):return re.sub('[^a-zA-Z0-9._-]+','_',s)[:130]
async def main():
 manifest=json.loads(MAN.read_text(encoding='utf-8')) if MAN.exists() else {}
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True);c=await b.new_context();page=await c.new_page()
  async def raw(url,title,category,expected=None):
   key=hashlib.sha256(url.encode()).hexdigest()[:12]
   if manifest.get(key,{}).get('status')=='ok':return
   row={'id':'support_'+key,'title':title,'source_url':url,'category':category,'retrieved_at':datetime.now(timezone.utc).isoformat()}
   try:
    r=await c.request.get(url,timeout=120000);body=await r.body();ct=r.headers.get('content-type','')
    if r.status!=200:raise RuntimeError(f'HTTP {r.status}')
    if 'html' in ct and expected!='html':raise RuntimeError('HTML returned instead of data')
    ext=expected or ('pdf' if body.startswith(b'%PDF') else 'xlsx' if body.startswith(b'PK') else 'xls' if body.startswith(bytes.fromhex('d0cf11e0')) else 'csv' if 'csv' in ct else 'bin')
    target=RAW/(key+'__'+slug(title)+'.'+ext);target.write_bytes(body)
    row.update(status='ok',local_path=target.relative_to(ROOT).as_posix(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),content_type=ct)
    print('SAVED',title,len(body),ext,flush=True)
   except Exception as e:row.update(status='error',error=str(e));print('ERROR',title,str(e),flush=True)
   manifest[key]=row;save(MAN,manifest)
  sfmta=json.loads((META/'web'/'sfmta_counts.json').read_text(encoding='utf-8'))
  for l in sfmta['links']:
   if '/media/' in l['url']:await raw(l['url'],l['text'],'traffic_counts')
  roots={'traffic':'https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer', 'datasf':'https://services.sfmta.com/arcgis/rest/services/DataSF/master/FeatureServer'}
  for group,num,name in [('traffic',7,'signal_inventory'),('traffic',9,'speed_limits'),('traffic',3,'traffic_lanes'),('traffic',5,'one_way_streets'),('datasf',35,'greenwave_signals'),('datasf',38,'greenwave_streets')]:
   url=roots[group]+'/'+str(num);await page.goto(url,wait_until='domcontentloaded')
   await raw(url+'?f=pjson',name+'_schema','gis_schema','json')
   # Public ArcGIS query operation exposed by the layer directory.
   count_r=await c.request.get(url+'/query',params={'where':'1=1','returnCountOnly':'true','f':'json'})
   count=await count_r.json(); print('GIS COUNT',name,count,flush=True)
   features=[];offset=0;error=None
   while True:
    r=await c.request.get(url+'/query',params={'where':'1=1','outFields':'*','outSR':'4326','returnGeometry':'true','f':'geojson','resultOffset':offset,'resultRecordCount':1000},timeout=60000)
    obj=await r.json()
    if 'error' in obj:error=obj['error'];break
    batch=obj.get('features',[]);features.extend(batch)
    if len(features)>=count.get('count',0) or not batch:break
    offset+=len(batch)
   qurl=url+'/query?where=1%3D1&outFields=*&outSR=4326&f=geojson'
   key=hashlib.sha256(qurl.encode()).hexdigest()[:12];target=RAW/(key+'__'+name+'.geojson')
   save(target,{'type':'FeatureCollection','features':features});body=target.read_bytes()
   manifest[key]={'id':'support_'+key,'title':name,'source_url':qurl,'category':'gis_context','retrieved_at':datetime.now(timezone.utc).isoformat(),'status':'ok' if not error else 'partial','local_path':target.relative_to(ROOT).as_posix(),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'feature_count':len(features),'expected_count':count.get('count'),'error':error};save(MAN,manifest)
  for name,url in [('cmp_dashboard','https://cmp.sfcta.org'),('congestion_dashboard','https://congestion.sfcta.org'),('sfcta_github','https://github.com/sfcta'),('dta_github','https://github.com/sfcta/dta')]:
   try:
    await page.goto(url,wait_until='domcontentloaded',timeout=60000);await page.wait_for_timeout(1200)
    text=await page.locator('body').inner_text();links=await page.locator('a[href]').evaluate_all('es=>es.map(e=>({title:e.innerText,url:e.href}))')
    save(META/'web'/(name+'.json'),{'url':url,'text':text,'links':links})
    print('PAGE',name,text[:90].encode('ascii','replace').decode(),flush=True)
    for l in links:
     if re.search('download|zip|csv|speed|data|cmp|dta',l['title']+' '+l['url'],re.I):print(json.dumps(l,ensure_ascii=True),flush=True)
   except Exception as e:print('PAGE ERROR',name,str(e),flush=True)
  await b.close()
if __name__=='__main__':asyncio.run(main())
