"""트랙 A(Kaggle) 공고 보정본 만들기. 원본은 바꾸지 않고 열을 추가한다. 분석용 스크립트(서비스 코드 아님)."""
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))) if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='extras' else _o.path.dirname(_o.path.abspath(__file__)))
from paths import *
import re, json, csv, collections
import numpy as np, pandas as pd

SRC = KAGGLE_CSV
OUT = TRACKA_CLEAN
df = pd.read_csv(SRC, low_memory=False)
P = json.load(open(POSTING_KW))  # P1 규칙으로 같은 파일에서 뽑은 역량 번호
D = {int(r['kw_idx']): (r['분류코드'], r['키워드']) for r in csv.DictReader(open(DICT_CSV, encoding='utf-8-sig'))}

title = df['채용공고제목'].fillna('').astype(str)
desc = df['채용공고상세내용'].fillna('').astype(str)
comp = df['기업명'].fillna('').astype(str)
is_hn = df['수집출처'].eq('hnhiring')

# ---------- 직무명 찾기 ----------
ROLE = re.compile(r"\b(engineer(?:ing)?|developer|programmer|scientist|analyst|designer|architect|manager|lead|director|intern(?:ship)?|recruiter|marketer|marketing|sales|account executive|writer|researcher|specialist|coordinator|technician|consultant|devops|sre|administrator|associate|representative|officer|nurse|agent)s?\b", re.I)
PERSON = re.compile(r"\b(engineer|developer|programmer|scientist|analyst|designer|architect|recruiter|marketer|researcher|technician|intern)s?\b", re.I)
LOC = re.compile(r"\b(remote|onsite|on-site|hybrid|full[- ]?time|part[- ]?time|contract|visa|usa?|united states|[A-Z][a-z]+,\s?[A-Z]{2})\b")

def hn_role(t, d):
    head = d[:400]
    segs = [s.strip() for s in head.split('|')[:7]]
    roles = [s for s in segs[1:] if ROLE.search(s) and len(s) < 120 and 'http' not in s]
    if roles:
        return roles[0]
    if ROLE.search(t) and not LOC.search(t):
        return t
    m = PERSON.search(d[:600])
    return d[max(0, m.start() - 40):m.end() + 10] if m else ''

role_text = np.where(is_hn, [hn_role(t, d) for t, d in zip(title, desc)], title)
role_text = pd.Series(role_text).fillna('').astype(str)

# ---------- 직무분류 다시 매기기 ----------
FAM_RULES = [  # 위에서부터 먼저 맞는 것
    ('non_target', r"security officer|security guard|border patrol|law enforcement|police|correctional|caregiver|cdl|truck driver|delivery driver|bank teller|relationship banker|financial solutions advisor|cashier|janitor|housekeep"),
    ('healthcare', r"\bnurse\b|\brn\b|\blpn\b|\bcna\b|medical assistant|clinical|therapist|technologist|radiolog|patholog|veterinar|dental|pharmac|physician|caregiv"),
    ('support', r"moderator"),
    ('sales', r"sales engineer|\bsales\b|account executive|business development|\bsdr\b|\bbdr\b|account manager"),
    ('hardware_engineering', r"aerodynamic|aerospace|thermal engineer|structures engineer|gnc|mechanical|electrical engineer|propulsion|civil engineer|chemical engineer|manufacturing engineer|hardware|controls engineer|avionics|structural engineer|industrial engineer|process engineer|quality engineer|rf engineer|test engineer \(hardware|mechatronic"),
    ('data_ai', r"data scien|data analy|data engineer|machine learning|\bml\b|\bai\b engineer|ai/ml|research scientist|analytics|business intelligence|\bbi\b|statistic|data platform|mlops|deep learning|nlp|computer vision"),
    ('design', r"designer|\bux\b(?! engineer)|user experience|product design|visual design"),
    ('marketing', r"marketing|growth|\bbrand|content|\bseo\b|social media|(?<!tele)communications|copywrit|\bpr\b|community manager"),
    ('product', r"product manager|product owner|program manager|\bpm\b"),
    ('people_hr', r"recruit|\btalent (?:acquisition|partner|sourc)|\bhr\b|human resources|people ops|people operations|compensation|benefits partner"),
    ('support', r"customer support|support engineer|customer success|customer service|help ?desk|technical support|moderator"),
    ('finance_legal', r"accountant|accounting|finance|financial analyst|legal|counsel|paralegal|bookkeep|controller"),
    ('operations', r"operations|\bops\b|logistics|supply chain|office manager|administrative|admin(?:istrative)? assistant|executive assistant"),
    ('software_engineering', r"software|engineer|developer|devops|\bsre\b|full.?stack|front.?end|back.?end|mobile|\bios\b|android|\bqa\b|test automation|programmer|infrastructure|platform|security engineer|firmware|embedded"),
]
FAM_RX = [(f, re.compile(p, re.I)) for f, p in FAM_RULES]
ENG = re.compile(r"engineer|developer|programmer", re.I)
NOT_IF_ENG = {'marketing', 'design', 'people_hr', 'operations', 'finance_legal'}

def first_chunk(r):
    parts = [p for p in re.split(r",|/|&|\+|\band\b|;|\(|\.\s", r) if ROLE.search(p)]
    return parts[0] if parts else r

def classify(r, t):
    for src, txt in (('직무명', first_chunk(r)), ('직무명', r), ('제목', t)):
        for f, rx in FAM_RX:
            if txt and rx.search(txt):
                if f in NOT_IF_ENG and ENG.search(txt):
                    continue
                return f, src
    return None, None

new_fam, fam_src = [], []
for r, t, old, how in zip(role_text, title, df['CareerLens직무분류'], df['직무분류방법']):
    f, s = classify(r, t)
    if f is None:
        f, s = (old, '원본유지(제목규칙)') if how == 'title_rule' else ('unclassified', '근거없음→미분류')
    new_fam.append(f); fam_src.append(s)
df['보정_직무명'] = role_text.str.slice(0, 120)
df['보정_직무분류'] = new_fam
df['보정_직무분류근거'] = fam_src
df['취준생대상외의심'] = (pd.Series(new_fam) == 'non_target').astype(int)

# ---------- HN 다중 직무 ----------
def multi_role(d):
    head = d[:700].lower()
    nouns = set(m.group(1).lower().rstrip('s') for m in ROLE.finditer(head))
    listy = re.search(r"(roles|positions|openings|hiring for|we'?re hiring)\s*[:\-]", head) is not None
    fams = {f for f, rx in FAM_RX[2:] if rx.search(head)}
    return int((listy and len(nouns) >= 2) or len(fams) >= 3)
df['다중직무공고의심'] = np.where(is_hn, [multi_role(d) for d in desc], 0)

# ---------- 중복 ----------
def norm_comp(s): return re.sub(r"\(.*?\)|[^a-z0-9]", "", s.lower())
def norm_role(s): return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
def shingles(s, k=5):
    w = re.findall(r"[a-z0-9]+", s.lower())[:300]
    return {' '.join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}
date = pd.to_datetime(df['표준공고등록일'], errors='coerce')
df['_c'] = comp.map(norm_comp); df['_r'] = role_text.map(norm_role)
dup_of = pd.Series([None] * len(df), dtype=object)
for (c, r), g in df.groupby(['_c', '_r']):
    if len(g) < 2 or not c:
        continue
    g = g.assign(_d=date[g.index]).sort_values('_d', ascending=False)
    keep = []
    for i in g.index:
        sh = shingles(desc[i])
        hit = next((k for k, ks in keep if len(sh & ks) / max(1, len(sh | ks)) >= 0.6), None)
        if hit is None:
            keep.append((i, sh))
        else:
            dup_of[i] = df.at[hit, 'CareerLens공고고유키']
df['중복여부'] = dup_of.notna().astype(int)
df['중복원본키'] = dup_of

# ---------- 역량 번호 ----------
kw_all = [p['kw'] for p in P]
score_kw = [[k for k in ks if D[k][0] not in ('C4', 'C5')] for ks in kw_all]
df['역량번호'] = [';'.join(map(str, ks)) for ks in kw_all]
df['역량명'] = [';'.join(D[k][1] for k in ks) for ks in kw_all]
df['세부기술'] = [';'.join(p['skills']) for p in P]
df['점수용역량수'] = [len(ks) for ks in score_kw]

# ---------- 신뢰도 ----------
tr = df['공고본문잘림의심여부'].fillna(0).astype(int)
n = df['점수용역량수']
df['공고신뢰도'] = np.select([(n >= 3) & (tr == 0), (n >= 2)], ['high', 'medium'], 'low')

# ---------- 트랙 A 사용 여부 ----------
df['트랙A사용'] = ((df['중복여부'] == 0) & (df['취준생대상외의심'] == 0)).astype(int)
df.drop(columns=['_c', '_r']).to_csv(OUT, index=False, encoding='utf-8-sig')

# ---------- 요약 ----------
S = {}
S['전체'] = len(df)
S['중복'] = int(df['중복여부'].sum())
S['취준생대상외'] = int(df['취준생대상외의심'].sum())
S['트랙A사용'] = int(df['트랙A사용'].sum())
S['다중직무의심(HN)'] = int(df['다중직무공고의심'].sum())
S['직무분류_바뀜'] = int((df['보정_직무분류'] != df['CareerLens직무분류']).sum())
S['분류근거'] = df['보정_직무분류근거'].value_counts().to_dict()
S['보정분류_사용공고'] = df.loc[df['트랙A사용'] == 1, '보정_직무분류'].value_counts().to_dict()
S['원본분류'] = df['CareerLens직무분류'].value_counts().to_dict()
S['신뢰도_사용공고'] = df.loc[df['트랙A사용'] == 1, '공고신뢰도'].value_counts().to_dict()
S['바뀜_상위'] = df.loc[df['보정_직무분류'] != df['CareerLens직무분류']].groupby(['CareerLens직무분류', '보정_직무분류']).size().sort_values(ascending=False).head(12).to_dict()
json.dump({k: (v if not isinstance(v, dict) else {str(a): b for a, b in v.items()}) for k, v in S.items()}, open(TRACKA_SUMMARY, 'w'), ensure_ascii=False, indent=1)
for k, v in S.items(): print(k, v)
