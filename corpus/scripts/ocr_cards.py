"""OCR only image-only pages in primary timing cards; originals stay intact."""
import json,re,sys
from pathlib import Path
import pymupdf as fitz
import numpy as np
from rapidocr_onnxruntime import RapidOCR
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'derived'/'ocr';OUT.mkdir(parents=True,exist_ok=True)
def main():
 manifest=json.loads((ROOT/'metadata'/'downloads.json').read_text(encoding='utf-8'));engine=RapidOCR(intra_op_num_threads=2,inter_op_num_threads=2)
 for row in manifest.values():
  if row.get('status')!='ok' or not row['local_path'].lower().endswith('.pdf'):continue
  if not (row['category']=='timing_card' or re.search(r'_Ch[_ ]*\d+',row['title'],re.I)):continue
  with fitz.open(ROOT/row['local_path']) as doc:
   for n,page in enumerate(doc):
    if len(re.sub(r'\s','',page.get_text()))>=80:continue
    target=OUT/(row['sha256'][:20]+f'_p{n+1}.json')
    if target.exists():continue
    pix=page.get_pixmap(matrix=fitz.Matrix(2.2,2.2),alpha=False)
    arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
    detections,elapsed=engine(arr[:,:,::-1])
    blocks=[{'box':b,'text':t,'confidence':float(score)} for b,t,score in (detections or [])]
    target.write_text(json.dumps({'document_id':row['id'],'pdf_page':n+1,'source_sha256':row['sha256'],'method':'RapidOCR ONNX local; machine transcription, unverified','blocks':blocks,'text':'\n'.join(x['text'] for x in blocks)},indent=2),encoding='utf-8')
    print('OCR',row['title'],n+1,len(blocks),flush=True)
if __name__=='__main__':main()
