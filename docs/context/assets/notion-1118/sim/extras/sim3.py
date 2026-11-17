import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
exec(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'sim_score.py')).read().split("nreq=")[0])
title=df['채용공고제목'].fillna('')
CORE={'C1','C2','C3','C7','C8'}
for name,(tgt,u) in users.items():
    rows=[]
    ucore={k for k in u if D[k][0] in CORE}
    for i,p in enumerate(P):
        req=[k for k in p['kw'] if D[k][0] not in('C4','C5')]
        if len(req)<=1: continue
        if not (set(req)&ucore): continue          # 후보: 내 핵심 역량과 1개 이상 겹침
        js=15 if fam[i]==tgt else (6 if fam[i] in ADJ.get(tgt,[]) else 0)
        vals=[COEF[u[k]] if k in u else 0 for k in req]
        fit=sum(vals)/max(len(vals),3); use=len(set(req)&set(u)); cov=np.mean([v>=0.5 for v in vals])
        rows.append((60*fit+js+career(i)+10,cov,len(req),fam[i],title[i][:60],use))
    r=pd.DataFrame(rows,columns=['tot','cov','n','fam','title','use']).sort_values(['tot','use','n'],ascending=False)
    print('\n==',name,'| 후보',len(r),'| 70점+&충족70%+',((r.tot>=70)&(r['cov']>=.7)).sum(),'| 55점+',(r.tot>=55).sum())
    for _,x in r.head(8).iterrows(): print(f'  {x.tot:5.1f} 충족{x["cov"]:.0%} 요구{x.n} [{x.fam}] {x.title}')
