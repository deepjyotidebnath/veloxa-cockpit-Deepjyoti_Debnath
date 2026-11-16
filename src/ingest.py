from pathlib import Path
import json
from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]; RAW=ROOT/'data/raw'; OUT=ROOT/'data/processed/evidence.jsonl'
RELEASES={'Day1_Mon_16Nov':'2026-11-16','Day2_Tue_17Nov':'2026-11-17','Day3_Wed_18Nov':'2026-11-18','Day4_Thu_19Nov':'2026-11-19'}
def extract(p):
 e=p.suffix.lower()
 if e=='.docx':
  d=Document(p); a=[x.text for x in d.paragraphs if x.text.strip()]
  for t in d.tables:
   for r in t.rows:a.append(' | '.join(c.text.replace('\n',' / ') for c in r.cells))
  return '\n'.join(a)
 if e=='.xlsx':
  w=load_workbook(p,data_only=True,read_only=True); a=[]
  for s in w:
   a.append('SHEET: '+s.title)
   for r in s.iter_rows(values_only=True):
    v=[str(x) if x is not None else '' for x in r]
    if any(v):a.append(' | '.join(v))
  return '\n'.join(a)
 if e=='.pdf':return '\n'.join(x.extract_text() or '' for x in PdfReader(str(p)).pages)
 if e in ('.eml','.txt','.csv'):return p.read_text(encoding='utf-8-sig',errors='replace')
 return ''
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True); rows=[]
 for p in sorted(RAW.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(RAW).as_posix(); txt=extract(p)
  if txt.strip():rows.append({'id':f'SRC-{len(rows)+1:03d}','source':rel,'release_date':RELEASES.get(rel.split('/')[0],'2026-11-16'),'text':txt})
 OUT.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
 print(f'Indexed {len(rows)} source files')
if __name__=='__main__':main()
