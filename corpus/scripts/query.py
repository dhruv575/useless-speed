"""Query all extracted PDF pages and workbook sheets with SQLite FTS5."""
import argparse,json,sqlite3,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('query',help='FTS5 query, e.g. "Ocean Avenue" or Synchro AND Existing');p.add_argument('--limit',type=int,default=15);p.add_argument('--json',action='store_true');args=p.parse_args()
database=ROOT/'derived'/'corpus.sqlite'
if not database.exists():p.error('Missing corpus.sqlite. Run git lfs pull first.')
with database.open('rb') as stream:
 if stream.read(16)!=b'SQLite format 3\x00':p.error('corpus.sqlite is not hydrated. Run git lfs pull first.')
con=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
try:
 rows=[dict(r) for r in con.execute('SELECT d.id,d.title,d.category,d.path,d.source_url,p.page,snippet(pages,2,"[", "]","…",32) AS excerpt FROM pages p JOIN documents d ON d.id=p.document_id WHERE pages MATCH ? ORDER BY rank LIMIT ?',(args.query,args.limit))]
except sqlite3.OperationalError as e:p.error(str(e))
if args.json:print(json.dumps(rows,indent=2,ensure_ascii=False))
else:
 for r in rows:print(f'{r["title"]} | page/sheet {r["page"]}\n  {r["excerpt"]}\n  {r["path"]}\n  {r["source_url"]}\n')
