"""Prepare compact public snapshots for the exploratory city simulator."""
import asyncio,hashlib,json,sys,statistics
from pathlib import Path
from datetime import datetime,timezone
from playwright.async_api import async_playwright
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
ROOT=Path(__file__).resolve().parents[1];APP=ROOT.parent/'app';OUT=APP/'public'/'data';OUT.mkdir(parents=True,exist_ok=True);(APP/'data').mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
async def main():
 manifest=read(ROOT/'metadata'/'supporting_downloads.json')
 def source(title):return read(ROOT/next(r['local_path'] for r in manifest.values() if r['title']==title))
 roads=source('speed_limits');kept=[]
 for f in roads['features']:
  p=f['properties'];s=p.get('SPEEDLIMIT') or 0
  if not (10<=s<=65):continue
  kept.append({'type':'Feature','geometry':f['geometry'],'properties':{'id':p['OBJECTID'],'cnn':p['CNN'],'name':((p.get('STREET') or '')+' '+(p.get('ST_TYPE') or '')).strip(),'limit':s,'status':p.get('STATUS'),'school':p.get('SCHOOLZONE_LIMIT'),'installed':p.get('INSTALL_DATE')}})
 save(OUT/'speed-limits.json',{'type':'FeatureCollection','features':kept})
 signals=source('signal_inventory');features=[]
 for f in signals['features']:
  p=f['properties']
  if p.get('TYPE') not in ['SIGNAL','CALTRANS','CALTRANS (BY CONTRACTOR CONSORTIUM GLC)','SIGNAL (CONTRACTOR MAINTAINED)']:continue
  features.append({'type':'Feature','geometry':f['geometry'],'properties':{'id':p['OBJECTID'],'cnn':str(p.get('CNN','')),'name':' & '.join(str(p.get(s,'')).strip() for s in ['STREET1','STREET2'] if str(p.get(s,'')).strip()),'system':p.get('SYSTEM_NUM'),'actuated':p.get('VEH_ACTUAT'),'priority':p.get('PREEMPT_PR')}})
 save(OUT/'signals.json',{'type':'FeatureCollection','features':features})
 # Local road geometry is also a basemap fallback if third-party tiles fail.
 roads=source('traffic_lanes');save(OUT/'streets.json',{'type':'FeatureCollection','features':[{'type':'Feature','geometry':f['geometry'],'properties':{'name':(str(f['properties'].get('STREET',''))+' '+str(f['properties'].get('ST_TYPE',''))).strip(),'class':f['properties'].get('CLASSCODE')}} for f in roads['features']]})
 monthly=read(ROOT/'raw'/'sfcta'/'inrix_rt_hourly_exp.json');latest=max(r['date'] for r in monthly)
 speeds={}
 for r in monthly:
  if r['date']!=latest or r.get('avg_speed') is None:continue
  try:hour=int(r['period'].strip())
  except:continue
  speeds.setdefault(str(r['cmp_segid']),{})[hour]=round(float(r['avg_speed']),2)
 segments=read(ROOT/'raw'/'sfcta'/'cmp_segments_exp.json');out=[]
 for s in segments:
  vals=speeds.get(str(s['cmp_segid']),{})
  if not vals:continue
  out.append({'type':'Feature','geometry':json.loads(s['geometry']) if isinstance(s['geometry'],str) else s['geometry'],'properties':{'id':s['cmp_segid'],'name':s['cmp_name'],'direction':s['direction'],'speeds':vals}})
 save(OUT/'observed-speeds.json',{'type':'FeatureCollection','period':latest,'features':out})
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True);c=await b.new_context()
  addresses=APP/'data'/'addresses.json'
  if not addresses.exists():
   rows=[];offset=0
   while True:
    r=await c.request.get('https://data.sfgov.org/resource/3mea-di5p.json',params={'$select':'eas_address_id,address,longitude,latitude,complete_landmark_name,landmark_aliases,nhood','$where':'longitude is not null AND latitude is not null','$order':'eas_address_id','$limit':50000,'$offset':offset},timeout=120000)
    if r.status!=200:raise RuntimeError(f'Address HTTP {r.status}')
    batch=await r.json();rows.extend(batch);await r.dispose();print('Addresses',len(rows),flush=True)
    if len(batch)<50000:break
    offset+=len(batch)
   save(addresses,rows)
  stops=OUT/'stop-signs.json'
  if not stops.exists():
   url='https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer/10'
   r=await c.request.get(url,params={'f':'json'});schema=await r.json();save(APP/'data'/'stop-sign-schema.json',schema)
   print('Stop sign fields',[f['name'] for f in schema.get('fields',[])],flush=True)
   allf=[];offset=0
   while True:
    r=await c.request.get(url+'/query',params={'where':'1=1','outFields':'*','outSR':4326,'f':'geojson','resultOffset':offset,'resultRecordCount':1000},timeout=60000)
    obj=await r.json();batch=obj.get('features',[])
    if 'error' in obj:raise RuntimeError(str(obj['error']))
    allf.extend(batch);offset+=len(batch)
    if not batch or not obj.get('exceededTransferLimit',False) and len(batch)<1000:break
   save(stops,{'type':'FeatureCollection','features':allf});print('Stop signs',len(allf),str(allf[0])[:1000],flush=True)
  # Public OSRM route for a reproducible first-load demonstration; same route
  # for both vehicles, with real geometry and maneuver data.
  demo=APP/'data'/'demo-route.json'
  if not demo.exists():
   url='https://router.project-osrm.org/route/v1/driving/-122.42844,37.75977;-122.41842,37.77927?overview=full&geometries=geojson&steps=true&annotations=distance,duration'
   r=await c.request.get(url,headers={'User-Agent':'UselessSpeedResearch/0.1 (local non-commercial simulation)'},timeout=90000)
   data=await r.json()
   if r.status!=200 or data.get('code')!='Ok':raise RuntimeError(str(data))
   save(demo,data);print('Demo route',data['routes'][0]['distance'],flush=True)
  await b.close()
 meta={'prepared_at':datetime.now(timezone.utc).isoformat(),'signal_features':len(features),'posted_speed_features':len(kept),'address_records':len(read(APP/'data'/'addresses.json')),'observed_speed_month':latest,'observed_segments':len(out),'sources':{'addresses':'https://data.sf.gov/d/3mea-di5p','signals':'https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer/7','speed_limits':'https://services.sfmta.com/arcgis/rest/services/Traffic/traffic/FeatureServer/9','observed_speeds':'https://congestion.sfcta.org','routing':'https://project-osrm.org'},'notes':['Signal inventory filtered to installed traffic-signal types, excluding pending signals and beacons.','Speed values 0/99 are missing/sentinel, not legal limits.','Observed speeds include intersection delay. They are a comparison benchmark, not a cruising-speed cap.']}
 save(OUT/'provenance.json',meta);print(meta,flush=True)
if __name__=='__main__':asyncio.run(main())
