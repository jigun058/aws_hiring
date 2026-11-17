import re
PROTECT = re.compile(r"tech stack|stack (?:includes|is)|our stack|we use|you(?:'ll| will)|roles?\b|looking to hire|hiring|engineers?\b|developers?\b|designers?\b|analysts?\b", re.I)
REQ = re.compile(r'experience (?:with|in|working)|proficien|familiar(?:ity)? with|knowledge of|required|requirements?|preferred|a plus|must have|must be|nice to have|bonus|skills? (?:in|with)|background in|ability to|years? of|you have|you\'ll need|qualifications|looking for|seeking|hiring', re.I)
# v1 (old)
BEN_V1 = re.compile(r'benefits|we offer|perks|401k|stipend|dental|vision|medical, |health insurance|disability insurance|life insurance|learning (?:and development )?budget|equipment budget', re.I)
COMP_V1 = re.compile(r'^(?:about us|we are|[a-z0-9 &.]+ is (?:a|an|the) )|used by|our (?:customers|clients|mission)|founded in', re.I)
# final
BEN_HEAD = re.compile(r'(?:competitive |great |excellent )?benefits (?:include|package|:)|what we offer|we offer:|perks(?: include|:)|what\'s in it for you|compensation (?:and|&) benefits|our benefits', re.I)
BEN_ITEMS = [r'401\(?k\)?', r'medical(?:,| &| and) dental', r'dental(?:,| &| and) vision', r'health insurance', r'life insurance', r'disability insurance', r'paid time off|\bpto\b', r'stipend', r'parental leave', r'learning (?:and development )?budget', r'equipment budget', r'gym membership', r'commuter benefits?']
BEN_ITEMS_RX = [re.compile(p, re.I) for p in BEN_ITEMS]
COMP_FINAL = re.compile(r'^(?:about (?:us|the company|the team)\b)|\bfounded in \d{4}|\bused by\b|\bbacked by\b|\bhas raised\b|\braised (?:over )?\$|\bour (?:customers|clients|mission|investors)\b|\bwe (?:help|build|are building|power|partner with)\b|\bwe(?:\'re| are) (?:a|an) (?:[a-z\-]+ ){0,3}(?:company|startup|team|platform|firm)\b|\bis (?:a|an) (?:leading |fast-growing |global |venture-backed )?(?:[a-z\-]+ ){0,3}(?:company|startup|platform|provider|firm)\b', re.I)
def is_benefit(s):
    """benefit sentence: header phrase, or >=2 benefit items. Never if the sentence carries a requirement signal (then only benefit spans are dropped)."""
    if REQ.search(s) or PROTECT.search(s):
        return False
    return bool(BEN_HEAD.search(s)) or sum(1 for r in BEN_ITEMS_RX if r.search(s)) >= 2
def benefit_spans(s):
    out = [m.span() for r in BEN_ITEMS_RX for m in r.finditer(s)]
    out += [m.span() for m in re.finditer(r'(?:medical|dental|vision|life|disability) (?:insurance|coverage)', s, re.I)]
    return out
def is_company(s):
    if REQ.search(s) or PROTECT.search(s):
        return False
    return bool(COMP_FINAL.search(s.strip()))
def mask(s, spans):
    s = list(s)
    for a, b in spans:
        for i in range(a, b): s[i] = ' '
    return ''.join(s)
