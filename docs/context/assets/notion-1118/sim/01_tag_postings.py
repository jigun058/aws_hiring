import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import sys, re, json, pandas as pd
sys.path.insert(0,HERE)
from p1_engine import map_en
df=pd.read_csv(KAGGLE_CSV,low_memory=False)
text=(df['채용공고제목'].fillna('')+' . '+df['채용공고상세내용'].fillna(''))
out=[]
for t in text:
    found=set(); sk=set()
    for s in re.split(r'(?<=[.!?])\s+|\s\|\s|\s[•*]\s',t):
        s=s.strip()
        if not s: continue
        o=map_en(s); found|=o['kw']; sk|=set(o['skills'])
    out.append({'kw':sorted(found),'skills':sorted(sk)})
json.dump(out,open(POSTING_KW,'w'))
print(len(out))
