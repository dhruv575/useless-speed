"""Read-only extraction, duplicate identification, FTS index and timing-page candidates.

Numeric cycle/offset fields are verbatim labeled values, not calibrated live
signal settings. Every candidate retains the original PDF and 1-based page.
"""
import csv,hashlib,json,re,sqlite3,sys,zipfile
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
import fitz,openpyxl
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
ROOT=Path(__file__).resolve().parents[1];META=ROOT/'metadata';DER=ROOT/'derived'
for p in [DER/'text',DER/'pages',DER/'workbooks',DER/'tables']:p.mkdir(parents=True,exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
def csvwrite(path,rows,fields=None):
 if not rows:return
 fields=fields or list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def manifests():
 out=[]
 for name in ['downloads','planning_downloads','supporting_downloads','speed_downloads','extra_downloads']:
  p=META/(name+'.json')
  if p.exists():out.extend(r for r in json.loads(p.read_text(encoding='utf-8')).values() if r.get('selected_for_corpus',True) and not re.search(r'^SFO |^Peninsula Pipelines',r['title']))
 for r in out:
  if r['id']=='43475468':r['category']='timing_card'
 return out
def extract(row):
 src=ROOT/row['local_path'];ext=src.suffix.lower();key=row['sha256'][:20]
 cache=DER/'pages'/(key+'.json')
 if cache.exists() and ext!='.csv':return json.loads(cache.read_text(encoding='utf-8'))
 result={'pages':[],'method':None};pages=result['pages']
 if ext=='.pdf':
  with fitz.open(src) as doc:
   result.update(page_count=len(doc),method='PyMuPDF text layer; no OCR')
   for n,page in enumerate(doc):pages.append({'page':n+1,'text':page.get_text(sort=True)})
  result['sparse_pages']=sum(len(re.sub(r'\s','',p['text']))<80 for p in pages)
 elif ext in ['.xlsx','.xlsm']:
  wb=openpyxl.load_workbook(src,read_only=True,data_only=False)
  values=openpyxl.load_workbook(src,read_only=True,data_only=True)
  sheets=[]
  for ws in wb:
   cells=[];lines=[]
   for rr in ws:
    parts=[]
    for cell in rr:
     if cell.value is None:continue
     cached=values[ws.title][cell.coordinate].value
     cells.append({'cell':cell.coordinate,'value_or_formula':cell.value,'cached_value':cached})
     parts.append(f'{cell.coordinate}={cached if cell.data_type=="f" else cell.value}')
    if parts:lines.append(' | '.join(parts))
   sheets.append({'sheet':ws.title,'cells':cells})
   pages.append({'page':len(pages)+1,'label':ws.title,'text':'SHEET '+ws.title+'\n'+'\n'.join(lines)})
  save(DER/'workbooks'/(key+'.json'),sheets);result.update(method='openpyxl sparse cells, formulas and cached values; no recalculation',sheets=len(sheets))
  wb.close();values.close()
 elif ext in ['.txt','.html','.htm']:
  text=src.read_text(encoding='utf-8',errors='replace')
  if ext in ['.html','.htm']:text=BeautifulSoup(text,'html.parser').get_text('\n')
  pages.append({'page':1,'text':text});result['method']='text/html extraction'
 elif ext=='.zip':
  with zipfile.ZipFile(src) as z:result['archive_members']=[{'name':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size} for i in z.infolist()]
  result['method']='ZIP member listing only; not expanded'
 elif ext in ['.json','.geojson']:
  obj=json.loads(src.read_text(encoding='utf-8-sig'))
  if isinstance(obj,list):
   result['row_count']=len(obj);result['fields']=list(obj[0]) if obj else []
   csvwrite(DER/'tables'/(src.stem+'.csv'),obj)
  elif obj.get('type')=='FeatureCollection':
   result['row_count']=len(obj['features']);result['fields']=list(obj['features'][0]['properties']) if obj['features'] else []
   csvwrite(DER/'tables'/(src.stem+'.csv'),[{'feature_id':f.get('id'),**f['properties'],'geometry':f.get('geometry')} for f in obj['features']])
  elif 'fields' in obj:result['fields']=[f['name'] for f in obj['fields']]
  result['method']='JSON schema and rows'
 elif ext=='.csv':
  try:src.read_text(encoding='utf-8-sig');encoding='utf-8-sig'
  except UnicodeDecodeError:encoding='cp1252'
  with src.open(encoding=encoding,newline='') as f:
   r=csv.reader(f);result['fields']=next(r,[]);result['row_count']=sum(1 for _ in r)
  (DER/'tables'/src.name).write_text(src.read_text(encoding=encoding),encoding='utf-8-sig')
  result['method']='CSV header and row count';result['source_encoding']=encoding
 else:result['method']='binary retained; requires native application'
 save(cache,result)
 if pages:(DER/'text'/(key+'.txt')).write_text('\n\n'.join(f'=== PAGE {p["page"]}'+(' / '+p['label'] if p.get('label') else '')+' ===\n'+p['text'] for p in pages),encoding='utf-8')
 return result

def main():
 rows=manifests();errors=[r for r in rows if r.get('status')!='ok'];docs=[dict(r) for r in rows if r.get('status')=='ok']
 seen={};candidates=[];unique_pages=0;sparse_pages=0;db=sqlite3.connect(DER/'corpus.sqlite')
 db.executescript('DROP TABLE IF EXISTS pages; DROP TABLE IF EXISTS documents; CREATE TABLE documents(id TEXT PRIMARY KEY,title TEXT,category TEXT,path TEXT,source_url TEXT,sha256 TEXT,duplicate_of TEXT); CREATE VIRTUAL TABLE pages USING fts5(document_id UNINDEXED,page UNINDEXED,text);')
 for row in docs:
  key=row['sha256'];row['duplicate_of']=seen.get(key);seen.setdefault(key,row['id'])
  db.execute('INSERT INTO documents VALUES(?,?,?,?,?,?,?)',(row['id'],row['title'],row['category'],row['local_path'],row['source_url'],key,row['duplicate_of']))
  try:
   result=extract(row)
   ocr_pages=0
   for page_item in result.get('pages',[]):
    ocrfile=DER/'ocr'/(key[:20]+f'_p{page_item["page"]}.json')
    if ocrfile.exists():
     ocr=json.loads(ocrfile.read_text(encoding='utf-8'));page_item['text']=ocr['text'];page_item['ocr']=True;ocr_pages+=1
   result['ocr_pages']=ocr_pages
   row['extraction']={k:v for k,v in result.items() if k not in ['pages','archive_members']}
   if ocr_pages:
    (DER/'text'/(key[:20]+'.txt')).write_text('\n\n'.join(f'=== PAGE {p["page"]}'+(' [MACHINE OCR]' if p.get('ocr') else '')+' ===\n'+p['text'] for p in result['pages']),encoding='utf-8')
   if result.get('pages'):row['text_path']='derived/text/'+key[:20]+'.txt'
   if result.get('sheets'):row['workbook_path']='derived/workbooks/'+key[:20]+'.json'
   if row['duplicate_of']:continue
   unique_pages+=result.get('page_count',0);sparse_pages+=result.get('sparse_pages',0)
   for p in result.get('pages',[]):
    t=p['text'];db.execute('INSERT INTO pages VALUES(?,?,?)',(row['id'],p['page'],t))
    # These labels are characteristic of Synchro worksheets, unlike generic
    # references to signals in narrative reports.
    cycles=[];act=[];offsets=[];timing_lines=[]
    for line in t.splitlines():
     label=re.search(r'\b((?:Actuated )?(?:Signal )?Cycle Length|Offset)(?:\s*[\[(](?:s|sec|seconds)[\])])?\s*(?::|=)?\s+(\d.*)',line,re.I)
     if label:
      numeric_run=re.match(r'[-+]?\d+(?:\.\d+)?(?:\s+[-+]?\d+(?:\.\d+)?)*',label[2])
      vals=re.findall(r'[-+]?\d+(?:\.\d+)?',numeric_run[0]) if numeric_run else []
      timing_lines.append(line.strip())
      (offsets if label[1].lower()=='offset' else act if label[1].lower().startswith('actuated') else cycles).extend(vals)
    primary_card=row['category']=='timing_card' or bool(re.search(r'_Ch[_ ]*\d+',row['title'],re.I))
    strong=bool(primary_card or cycles or act or offsets or re.search(r'signal timing (?:card|sheet)|coordination timing|CYCLE\s+OFFSET|SYSTEM\s+OFFSET',t,re.I))
    signals=bool(strong or re.search(r'synchro|signal.{0,30}timing|cycle length|total split|phase.{0,20}duration|coordination.{0,20}plan',t,re.I))
    if not signals:continue
    headings=[line.strip() for line in t.splitlines() if re.match(r'^\s*\d+\s*:\s*.{3,140}',line)][:5]
    conditions=[line.strip() for line in t.splitlines() if re.search(r'existing|baseline|future|cumulative|plus project|no.project|build|AM Peak|PM Peak',line,re.I) and len(line)<200][:8]
    hits=[]
    for m in list(re.finditer(r'cycle length|\boffset\b|signal timing|synchro|total split',t,re.I))[:4]:hits.append(re.sub(r'\s+',' ',t[max(0,m.start()-70):m.end()+160]))
    candidates.append({'document_id':row['id'],'title':row['title'],'category':row['category'],'pdf_page':p['page'],'source_url':row['source_url'],'local_path':row['local_path'],'heading_candidates':headings,'scenario_context':conditions,'cycle_length_seconds_candidates':cycles,'actuated_cycle_seconds_candidates':act,'offset_seconds_candidates':offsets,'verbatim_timing_lines':timing_lines,'strength':'labeled_timing' if strong else 'timing_mention','machine_ocr':bool(p.get('ocr')),'snippets':hits})
   print('INDEXED',row['id'],len(result.get('pages',[])),flush=True)
  except Exception as e:row['extraction_error']=str(e);print('EXTRACTION ERROR',row['id'],str(e),flush=True)
 db.commit();db.close()
 save(DER/'catalog.json',docs);save(DER/'timing_pages.json',candidates);save(META/'failures.json',errors)
 csvwrite(DER/'timing_pages.csv',candidates)
 csvwrite(DER/'catalog.csv',[{k:v for k,v in r.items() if k not in ['extraction']} for r in docs])
 unique=[r for r in docs if not r['duplicate_of']]
 ocr_count=sum(r.get('extraction',{}).get('ocr_pages',0) for r in unique)
 stats={'built_at':datetime.now(timezone.utc).isoformat(),'source_files':len(docs),'unique_files':len(unique),'duplicates':len(docs)-len(unique),'total_bytes':sum(r['bytes'] for r in docs),'unique_bytes':sum(r['bytes'] for r in unique),'unique_pdf_pages':unique_pages,'sparse_pdf_pages_without_ocr':sparse_pages-ocr_count,'ocr_pages':ocr_count,'timing_candidate_pages':len(candidates),'labeled_timing_pages':sum(r['strength']=='labeled_timing' for r in candidates),'cycle_length_pages':sum(bool(r['cycle_length_seconds_candidates'] or r['actuated_cycle_seconds_candidates']) for r in candidates),'by_category':dict(Counter(r['category'] for r in unique)),'by_extension':dict(Counter(Path(r['local_path']).suffix.lower() for r in unique)),'download_errors':len(errors),'extraction_errors':sum('extraction_error'in r for r in docs)}
 save(DER/'statistics.json',stats);print(json.dumps(stats,indent=2),flush=True)
if __name__=='__main__':main()
