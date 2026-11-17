import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import json, pandas as pd, numpy as np, csv, collections
df=pd.read_csv(KAGGLE_CSV,low_memory=False)
P=json.load(open(POSTING_KW))
D={int(r['kw_idx']):(r['분류코드'],r['키워드']) for r in csv.DictReader(open(DICT_CSV,encoding='utf-8-sig'))}
COEF={'L3':1.0,'L2':0.75,'L1':0.5}
ADJ={'data_ai':['software_engineering'],'software_engineering':['data_ai'],'marketing':['sales','product','design'],'sales':['marketing','support','product']}
users={
 '데이터분석 지망':('data_ai',{41:'L3',40:'L2',43:'L3',172:'L3',115:'L2',36:'L2',156:'L3',150:'L2'}),
 '프론트엔드 지망':('software_engineering',{44:'L3',111:'L2',15:'L2',49:'L1',156:'L2'}),
 '마케팅 지망':('marketing',{118:'L3',117:'L2',119:'L3',13:'L1',121:'L2',170:'L3',36:'L2',51:'L2'}),
}
lvl=df['CareerLens경력수준'].fillna('unknown'); yrs=df['CareerLens최소경력연수']; fam=df['CareerLens직무분류']; trunc=df['공고본문잘림의심여부']
def career(i):
    if not np.isnan(yrs[i]): return {1:14,2:11,3:7}.get(int(yrs[i]),7)
    return {'entry':15,'mid':5,'experienced':5}.get(lvl[i],9)
nreq=[len([k for k in p['kw'] if D[k][0] not in('C4','C5')]) for p in P]
print('postings req count: median',np.median(nreq),'p25',np.percentile(nreq,25),'p75',np.percentile(nreq,75),'zero',sum(n==0 for n in nreq),'<=1',sum(n<=1 for n in nreq))
for name,(tgt,u) in users.items():
    rows=[]
    for i,p in enumerate(P):
        f=fam[i]
        if f==tgt: js=15
        elif f in ADJ.get(tgt,[]): js=6
        else: continue
        req=[k for k in p['kw'] if D[k][0] not in('C4','C5')]
        if len(req)<=1: rows.append(('확인 필요(신뢰도 low)',None,None,f)); continue
        vals=[COEF[u[k]] if k in u else 0 for k in req]
        fit=np.mean(vals); cov=np.mean([v>=0.5 for v in vals])
        tot=60*fit+js+career(i)+10
        if tot>=70 and cov>=0.7: g='추천'
        elif tot>=55 and cov>=0.5: g='도전'
        else: g='미노출'
        rows.append((g,tot,len(req),f))
    r=pd.DataFrame(rows,columns=['g','tot','nreq','fam'])
    print('\n==',name,'후보',len(r),'| 같은 직무군',(r.fam==tgt).sum())
    print(r.g.value_counts().to_dict())
    t=r.dropna()
    print('점수 분포 p50/p90/max',round(t.tot.median(),1),round(t.tot.quantile(.9),1),round(t.tot.max(),1),'| 요구역량 수 중앙값',t.nreq.median())
    print('상위10 점수',[round(x,1) for x in sorted(t.tot,reverse=True)[:10]])
