"""Reference implementation of P1-final mapping rules, used ONLY to verify the spec (not service code)."""
import re, json, sqlite3, sys
import pandas as pd
import os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from p1_aliases_v1 import A as A1, KO_ADD as KO1
from p1_filters import is_benefit, is_company, benefit_spans, mask
from p1_rule175 import classify_final, KO as KO175

A = {k: list(v) for k, v in A1.items()}
A[15] = [x for x in A[15] if x != 'git']
A[44] = [x if x != "react(?:\\.js)?" else "react(?!\\s?native)(?:\\.js)?" for x in A[44]]
A[44] = [x for x in A[44] if x != 'c#']            # C# handled by CTX-CSHARP
A[46] = ["aws", "amazon web services", "gcp", "google cloud(?: platform)?", "azure", "serverless", "cloud (?:platforms?|services|infrastructure|computing|providers?|environments?|native|technologies|architecture)"]
A[175] = []                                         # handled by rule175
KO = dict(KO1)
KO[22] = ''; KO[128] = ''                           # 소방안전관리자: license only
KO[8] = ''; KO[85] = ''                             # 조리사 면허 -> via license rule
CERT_EXTRA = [(r'운전면허', [67], '자동차운전면허'), (r'조리사', [85, 8], '조리사'), (r'전기(?:\(?산업\)?)?기사', [20, 104], '전기(산업)기사')]  # last: fixes courses.json pattern bug   # proposed additions to cert rules

SKILLS = [  # (name, en regex, parent kw or None, context requirement)
 ("React Native", r"react\s?native", 179, None), ("React", r"react(?:\.js)?", 44, None),
 ("Next.js", r"next\.js", 44, None), ("Node.js", r"node\.?js|\bnode\b", 44, None),
 ("TypeScript", r"typescript", 44, None), ("JavaScript", r"javascript", 44, None),
 ("MariaDB", r"mariadb", 41, None), ("MySQL", r"mysql", 41, None), ("PostgreSQL", r"postgres(?:ql)?", 41, None),
 ("SQL Server", r"sql server|t-sql", 41, None),
 ("AWS Lambda", r"aws lambda|lambda functions? on aws", 46, None), ("Amazon S3", r"amazon s3|aws s3|s3 buckets?", 46, None),
 ("Amazon EC2", r"amazon ec2|aws ec2|ec2 instances?", 46, None),
 ("S3(문맥 필요)", r"\bs3\b", 46, r"aws|amazon"), ("Lambda(문맥 필요)", r"\blambda\b", 46, r"aws|amazon"), ("EC2(문맥 필요)", r"\bec2\b", 46, r"aws|amazon"),
 ("AWS", r"\baws\b|amazon web services", 46, None), ("GCP", r"\bgcp\b|google cloud", 46, None), ("Azure", r"\bazure\b", 46, None),
 ("GitHub", r"github", None, None), ("Git", r"\bgit\b", None, None),
 ("Docker", r"docker", 47, None), ("Kubernetes", r"kubernetes|\bk8s\b|\bhelm\b", 47, None),
 ("Snowflake", r"snowflake", 16, None), ("Power BI", r"power ?bi", 43, None), ("Tableau", r"tableau", 43, None),
 ("Swift/SwiftUI", r"swift(?:ui)?", 179, None), ("Cypress", r"cypress", 181, None), ("Selenium", r"selenium", 181, None),
 ("Django", r"django", 40, None), ("Scrapy", r"scrapy", 113, None), ("Figma", r"figma", 49, None), ("Storybook", r"storybook", 44, None),
 ("PHP", r"\bphp\b", 44, None), ("C++", r"c\+\+", 45, None), ("Python", r"python", 40, None), ("SQL", r"\bsql\b", 41, None),
]
SKILLS.sort(key=lambda x: -len(x[0]) if x[0] not in ("React", "SQL") else 0)  # longest names first; generic ones last
SKILLS = sorted(SKILLS, key=lambda x: (x[0] in ("React", "SQL", "AWS", "Git"), -len(x[1])))

SKILL_RX = [(n, re.compile(r'(?<![a-z0-9])(?:' + rx + r')(?![a-z0-9])', re.I), par, ctx) for n, rx, par, ctx in SKILLS]
def comp(p): return re.compile(r'(?<![a-z0-9])(?:' + '|'.join(p) + r')(?![a-z0-9])') if p else None
A[111] = A[111] + ["(?:on|in|with) the back[- ]?end", "back[- ]?end (?:systems|services)"]
A[110] = A.get(110, []) + ["(?:hardware|avionics|electrical|vehicle|rf|mechanical|systems) test(?:ing)? engineers?", "(?:hardware|avionics) testing"]
A[166] = ["manufacturing (?:processes|operations|engineering|lines?|experience|environment)", "production lines?", "lean manufacturing", "six sigma"]
RX = {i: comp(p) for i, p in A.items() if p}
SECX = re.compile(r'security (?:officer|guard|clearance)|social security|national security', re.I)
LIC_EN = re.compile(r'(?:\b[\w\-]+ ){0,2}licen[sc]e[sd]?\b|(?:\b[\w\-]+ ){0,2}certification', re.I)
DEG_EN = re.compile(r'(?:degree|bachelor\'?s?|master\'?s?|ph\.?d\.?)(?: degree)? in [\w ,&]+?(?:field|or a related[\w ]*|$)', re.I)

def csharp_ctx(s):
    l = s.lower()
    if not re.search(r'c#|\.net', l): return None
    if re.search(r'unity|game|게임|wpf|winforms|desktop|데스크톱', l): return 111
    if re.search(r'embedded|firmware|plc|설비|제어|임베디드|hmi', l): return 45
    return 44

def map_en(s):
    out = {"kw": set(), "skills": [], "non": []}
    if is_benefit(s): out["non"].append("benefit"); return out
    if is_company(s): out["non"].append("company"); return out
    t = s
    for m in LIC_EN.finditer(t): out["non"].append("license:" + m.group(0).strip())
    t = mask(t, [m.span() for m in LIC_EN.finditer(t)])
    t = mask(t, [m.span() for m in DEG_EN.finditer(t)] + benefit_spans(t))
    low = t.lower()
    low = re.sub(r'(?<=[a-z])/(?=[a-z]{3,})(?!cd|ip)', ' ', low)   # data/analysis -> data analysis (keeps ci/cd, tcp/ip)
    for name, r, par, ctx in SKILL_RX:                # longest-match-first with masking
        hits = list(r.finditer(low))
        if not hits: continue
        if ctx and not re.search(ctx, low): continue
        out["skills"].append(name)
        if par is not None: out["kw"].add(par)
        low = mask(low, [h.span() for h in hits])
    for i, r in RX.items():
        if r.search(low):
            if i == 17 and SECX.search(s): continue
            out["kw"].add(i)
    if re.search(r'\bGo\b', s) and re.search(r'Kubernetes|Python|Java|Rust|Node|Helm', s): out["kw"].add(44)
    c = csharp_ctx(s)
    if c: out["kw"].add(c); out["skills"].append("C#")
    if re.search(r'(?<![a-z])qa(?![a-z])', s.lower()) and 99 in out["kw"]:
        if re.search(r'software|code|test|automation|app|web|bug', s, re.I): out["kw"].discard(99); out["kw"].add(181)
        elif not re.search(r'product|quality (?:assurance|control)|inspection|gmp', s, re.I): out["kw"].discard(99); out["non"].append("unclassified:QA")
    r175 = classify_final(s)
    if r175: out["kw"].add(r175)
    return out

_con = sqlite3.connect('file:' + _os.environ.get('CAREERLENS_DB', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'careerlens.db')) + '?mode=ro', uri=True)
_k = pd.read_sql('select keyword,synonyms,match_patterns from keywords order by keyword_id', _con)
_rules = [r for r in json.load(open(_os.environ.get('COURSES_JSON', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'courses.json')), encoding='utf-8'))['rules'] if r[2]]
MAJOR = re.compile(r'[가-힣A-Za-z·]+\s?(?:공학\s?)?(?:전공자|전공|학과)')
_lic = pd.read_sql('select license_name from licenses where is_qualification=1', _con).license_name
LIC_NAMES = re.compile('|'.join(r'\s?'.join(map(re.escape, n)) + r'(?:\s?(?:특급|\d급))?' for n in sorted(_lic, key=len, reverse=True) if len(n) >= 4))
LIC_KO = re.compile(r'[가-힣A-Za-z0-9]+(?:\s?\d급|\s?특급)?\s?(?:자격증|면허증|면허|기능사|산업기사|기사)')

def map_ko(s):
    out = {"kw": set(), "skills": [], "non": []}
    for m in LIC_KO.finditer(s): out["non"].append("license:" + m.group(0))
    for m in MAJOR.finditer(s): out["non"].append("major:" + m.group(0))
    s2 = MAJOR.sub(' ', s)
    spans = [m.span() for m in LIC_KO.finditer(s2)] + [m.span() for m in LIC_NAMES.finditer(s2)]
    lic = [s2[a:b] for a, b in spans]
    out['non'] += ['license:' + x for x in lic]
    t = mask(s2, spans)
    m = re.search(r'복리후생|복지\s?:|혜택\s?:', t)            # CTX-BENEFIT-KO: drop benefit section
    if m: t = t[:m.start()]
    t = re.sub(r'4대\s?보험\s?(?:가입|적용|완비)', ' ', t)
    tc = t.replace(' ', '')
    for L in lic:                                   # license -> implied competency only via cert rules
        for pat, ids, _ in _rules + CERT_EXTRA:
            if re.search(pat, L): out["kw"] |= set(ids); out["skills"].append("license_implied")
    for i, row in _k.iterrows():
        syns = [x for x in (row.synonyms or '').split('|') if x] + [x for x in KO.get(i, '').split('|') if x]
        if any(x in t for x in syns) or any(' ' in x and x.replace(' ', '') in tc for x in syns) or (isinstance(row.match_patterns, str) and any(re.search(p, t) for p in row.match_patterns.split(' || '))):
            out["kw"].add(i)
    for pat, ids, _ in _rules + CERT_EXTRA:
        if re.search(pat, t): out["kw"] |= set(ids)
    if '식품위생' in t and not re.search(r'(?<!식품)위생 관리|소독|청결', t): out["kw"].discard(88)
    if '재단' in t and re.search(r'필름|원단|롤|슬리터|기계', t) and not re.search(r'의류|봉제|패턴|미싱', t): out["kw"].discard(134); out["kw"].add(102)
    if re.search(r'재단기|슬리터', t): out["kw"].add(100)
    if re.search(r'도면\s?(?:확인|해독|검토|보고|숙지)', t) and not re.search(r'도면\s?(?:작성|설계|제도)|설계', t): out["kw"].discard(107)   # reading drawings != drafting
    c = csharp_ctx(t)
    if c: out["kw"].discard(45); out["kw"].add(c)
    if KO175.search(t): out["kw"].add(175)
    return out

def map_sentence(s, track):
    return map_en(s) if track == 'A' else map_ko(s)
