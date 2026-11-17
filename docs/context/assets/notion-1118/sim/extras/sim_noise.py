import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import sys,re,json,pandas as pd
sys.path.insert(0,'.')
import p1_engine as E
df=pd.read_csv(KAGGLE_CSV,low_memory=False)
P=json.load(open(POSTING_KW))
for k in [13,95,91,11,24,103,5,12]:
    print(k, E.A.get(k)[:12] if E.A.get(k) else E.A.get(k))
fam=df['CareerLens직무분류']; text=(df['채용공고제목'].fillna('')+' . '+df['채용공고상세내용'].fillna(''))
m=fam=='marketing'
print('marketing postings with word marketing:', text[m].str.contains('marketing',case=False).mean())
print('titles sample:', df.loc[m,'채용공고제목'].sample(15,random_state=1).tolist())
# which sentences trigger 95 / 91 / 11 in data_ai
import random
for k in [95,91,11,24,103]:
    ex=[]
    for i in df.index[fam.isin(['data_ai','marketing'])]:
        if k in P[i]['kw']:
            for s in re.split(r'(?<=[.!?])\s+|\s\|\s|\s[•*]\s',text[i]):
                if k in E.map_en(s.strip())['kw']: ex.append(s.strip()[:150]); break
        if len(ex)>=4: break
    print('\n',k,ex)
