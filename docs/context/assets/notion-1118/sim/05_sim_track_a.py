import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import pandas as pd, numpy as np, csv, json
df=pd.read_csv(TRACKA_CLEAN,low_memory=False)
D={int(r['kw_idx']):(r['분류코드'],r['키워드']) for r in csv.DictReader(open(DICT_CSV,encoding='utf-8-sig'))}
COEF={'L3':1.0,'L2':0.75,'L1':0.5}; CORE={'C1','C2','C3','C7','C8'}
ADJ={'data_ai':['software_engineering'],'software_engineering':['data_ai','hardware_engineering'],'marketing':['sales','product','design']}
users={'데이터분석 지망':('data_ai',{41:'L3',40:'L2',43:'L3',172:'L3',115:'L2',36:'L2',156:'L3',150:'L2'}),
 '프론트엔드 지망':('software_engineering',{44:'L3',111:'L2',15:'L2',49:'L1',156:'L2'}),
 '마케팅 지망':('marketing',{118:'L3',117:'L2',119:'L3',13:'L1',121:'L2',170:'L3',36:'L2',51:'L2'})}
def career(r):
    y=r['CareerLens최소경력연수']
    if not pd.isna(y): return {1:14,2:11,3:7}.get(int(y),7)
    return {'entry':15,'mid':5,'experienced':5}.get(r['CareerLens경력수준'],9)
u=df[df['트랙A사용']==1]
for name,(tgt,us) in users.items():
    ucore={k for k in us if D[k][0] in CORE}; rows=[]
    for _,r in u.iterrows():
        req=[int(k) for k in str(r['역량번호']).split(';') if k and k!='nan']
        req=[k for k in req if D[k][0] not in('C4','C5')]
        if len(req)<=1 or not set(req)&ucore: continue
        js=15 if r['보정_직무분류']==tgt else (6 if r['보정_직무분류'] in ADJ.get(tgt,[]) else 0)
        vals=[COEF[us[k]] if k in us else 0 for k in req]
        fit=sum(vals)/max(len(vals),3); cov=np.mean([v>=.5 for v in vals]); use=len(set(req)&set(us))
        rows.append((60*fit+js+career(r)+10,cov,use,len(req),r['공고신뢰도'],r['보정_직무분류'],str(r['채용공고제목'])[:40],str(r['보정_직무명'])[:45],r['기업명']))
    t=pd.DataFrame(rows,columns=['tot','cov','use','n','rel','fam','title','role','co']).sort_values(['tot','use','n'],ascending=False)
    t=t.drop_duplicates(['co','title'])
    print(f"\n== {name} | 후보 {len(t)} | 70점+ {(t.tot>=70).sum()} | 60점+ {(t.tot>=60).sum()} | 55점+ {(t.tot>=55).sum()}")
    for _,x in t.head(6).iterrows(): print(f"  {x.tot:5.1f} 충족{x['cov']:.0%} 요구{x.n} [{x.fam[:10]}] {x.title} / {x.role}")
