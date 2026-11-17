import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
exec(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'sim_score.py')).read().split("for name,(tgt,u)")[0])
for name,(tgt,u) in users.items():
    c=collections.Counter(); n=0
    for i,p in enumerate(P):
        if fam[i]!=tgt: continue
        n+=1
        for k in p['kw']:
            if D[k][0] in('C4','C5'): continue
            c[k]+=1
    print('\n==',name,tgt,n)
    print([(k,D[k][1],D[k][0],round(v/n*100),'보유' if k in u else '') for k,v in c.most_common(18)])
