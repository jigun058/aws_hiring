import math
import re
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

import knowledge as K
import licenses_kb as L
from common import OUT, TODAY, WORK

WEIGHTS = dict(keyword=0.30, semantic=0.25, action=0.20, experience=0.15, qualification=0.10)
IMP_W = {"required": 1.0, "major": 0.75, "supplementary": 0.45}
MATCH_W = {"synonym": 1.0, "direct": 1.0, "derived": 0.7, "transferable": 0.45}
ACTION_CATS = {"C2", "C3", "C7"}
TOP_K = 10
MIN_SCORE = 30.0
REL_CUT = 0.72
SEM_SCALE = 0.35


class CareerMatcher:
    def __init__(self, out_dir=OUT):
        self.kw = pd.read_csv(out_dir / "keywords.csv")
        self.occ = pd.read_csv(out_dir / "occupations.csv")
        self.prof = pd.read_csv(out_dir / "occupation_keyword_profile.csv")
        self.rel = pd.read_csv(out_dir / "keyword_relations.csv")
        self.olic = pd.read_csv(out_dir / "occupation_licenses.csv")
        self.opref = pd.read_csv(out_dir / "occupation_preferences.csv")
        self.lic = pd.read_csv(out_dir / "licenses.csv")
        self.posts = pd.read_pickle(WORK / "s02_postings.pkl")
        self.pkw = pd.read_pickle(WORK / "s02_posting_keywords.pkl")
        self.cat = dict(zip(self.kw.keyword, self.kw.category_code))
        self.disc = dict(zip(self.kw.keyword, self.kw.discriminative_weight))
        self.common = set(self.kw.loc[self.kw.is_common_competency, "keyword"])
        self.lex = K.compile_lexicon(K.load_keywords())
        self.rules = [(r, [re.compile(p) for p in r["all_of"]]) for r in K.EXPERIENCE_RULES]
        self.related = defaultdict(list)
        for r in self.rel.itertuples():
            self.related[r.keyword_a].append((r.keyword_b, r.weight))
            self.related[r.keyword_b].append((r.keyword_a, r.weight))
        self.occ_ids = list(self.occ.occupation_id)
        self.occ_idx = {o: i for i, o in enumerate(self.occ_ids)}
        self.kw_list = list(self.kw.keyword)
        self.kw_idx = {k: i for i, k in enumerate(self.kw_list)}
        W = np.zeros((len(self.occ_ids), len(self.kw_list)))
        IMPN = np.zeros_like(W)
        for r in self.prof.itertuples():
            i, j = self.occ_idx[r.occupation_id], self.kw_idx[r.keyword]
            W[i, j] = IMP_W[r.importance] * r.combined_score * self.disc[r.keyword]
            IMPN[i, j] = IMP_W[r.importance]
        self.W, self.IMPN = W, IMPN
        topk = np.argsort(-W, axis=1)[:, :TOP_K]
        self.topmask = np.zeros_like(W, dtype=bool)
        np.put_along_axis(self.topmask, topk, True, axis=1)
        self.topmask &= W > 0
        self.fam = self.occ.job_family_id.values
        denom = (W * self.topmask).sum(axis=1)
        self.k_denom = np.maximum(denom, 0.6 * np.median(denom[denom > 0]))
        valid = self.posts[~self.posts.is_exact_duplicate]
        cs = valid.assign(c=valid["경력"].eq("경력")).groupby("occupation_id")["c"].mean()
        self.career_share = np.array([cs.get(o, 0.0) for o in self.occ_ids])
        n_post = self.occ.posting_count.values
        self.reliability = 0.9 + 0.1 * np.minimum(1, np.log10(n_post + 1) / np.log10(31))
        senior_name = self.occ.occupation_name.str.contains(r"관리자|부서장|소장|주방장|감독|임원|반장|강사$|강사\)|교육 전문가|컨설턴트")
        self.senior = (self.occ.major_code.astype(str).eq("0") & self.occ.minor_code.astype(str).isin(["1", "01"])) | senior_name
        self.senior = self.senior.values
        self.base_names = [re.sub(r"\(.*?\)", "", n).strip() for n in self.occ.occupation_name]
        self.top_sets = [set(np.array(self.kw_list)[self.topmask[i]]) for i in range(len(self.occ_ids))]
        self._build_semantic()
        self._build_license_index()

    def _build_semantic(self):
        valid = self.posts[~self.posts.is_exact_duplicate]
        samp = valid.dropna(subset=["duty_text"]).groupby("occupation_id")["duty_text"].apply(lambda s: " ".join(x[:200] for x in s.head(20)))
        docs = []
        for r in self.occ.itertuples():
            p = self.prof[self.prof.occupation_id == r.occupation_id]
            kwtxt = " ".join((row.keyword + " ") * (2 if row.importance == "required" else 1) for row in p.itertuples())
            docs.append(f"{r.occupation_name} {str(r.original_occupation_names).replace('|', ' ')} {r.job_family_name} {kwtxt} {samp.get(r.occupation_id, '')}")
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, min_df=2)
        self.D = self.vec.fit_transform(docs)

    def _build_license_index(self):
        self.lic_names = sorted(self.lic.loc[self.lic.is_qualification, "license_name"], key=len, reverse=True)
        self.legal = self.olic[self.olic.requirement_type.isin(["필수(법정)", "필수(법정·조건부)"])]
        self.practice = self.olic[self.olic.requirement_type == "필수(채용관행)"]

    def extract(self, text):
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
        ctx_name, ctx_w = K.DEFAULT_CONTEXT
        for name, pat, w in K.EXPERIENCE_CONTEXTS:
            if re.search(pat, text):
                ctx_name, ctx_w = name, w
                break
        found = {}
        activities, actions, achievements = [], [], []
        for s in sents:
            ach = self._achievements(s)
            achievements += ach
            learned = bool(re.search(K.LEARN_ONLY, s)) and not re.search(K.PERFORMED, s)
            strength = 1.0 if ach else (0.5 if learned else 0.75)
            for kw, pat in self.lex:
                if pat.search(s):
                    self._add(found, kw, "synonym", strength, s)
            for r, pats in self.rules:
                if all(p.search(s) for p in pats):
                    activities.append(r["activity"])
                    actions.append(r["action"])
                    for kw, mt in r["kw"].items():
                        self._add(found, kw, mt, strength, s, r["id"])
        licenses = self._licenses(text)
        majors = re.findall(r"([가-힣A-Za-z·]+)\s?(?:관련\s?)?(?:전공|학과)", text)
        return dict(text=text, context=ctx_name, context_weight=ctx_w, activities=list(dict.fromkeys(activities)),
                    actions=list(dict.fromkeys(actions)), achievements=achievements, keywords=found, licenses=licenses, majors=majors)

    def _add(self, found, kw, mt, strength, sent, rule=None):
        w = MATCH_W[mt]
        cur = found.get(kw)
        if cur is None or w > cur["match_weight"] or (w == cur["match_weight"] and strength > cur["evidence_strength"]):
            found[kw] = dict(keyword=kw, category=K.CATEGORIES[self.cat[kw]], match_type=mt, match_weight=w,
                             evidence_strength=strength, evidence=sent, rule=rule)

    @staticmethod
    def _achievements(s):
        out = []
        for m in re.finditer(r"(\d[\d,]*)\s*(명|개|건|회|원|만원|%|점|명의)?\s*에서\s*(\d[\d,]*)\s*(명|개|건|회|원|만원|%|점)?", s):
            a, b = float(m.group(1).replace(",", "")), float(m.group(3).replace(",", ""))
            if a > 0:
                out.append(dict(type="증감", text=m.group(0), before=a, after=b, change_pct=round((b - a) / a * 100, 1)))
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%\s*(증가|향상|상승|개선|감소|절감|단축)", s):
            out.append(dict(type="비율", text=m.group(0), change_pct=float(m.group(1)) * (-1 if m.group(2) in ("감소", "절감", "단축") else 1)))
        for m in re.finditer(r"(대상|최우수상|우수상|금상|은상|동상|장려상|입상|수상|\d+위)", s):
            out.append(dict(type="수상·순위", text=m.group(0)))
        return out

    def _licenses(self, text):
        held = []
        if not re.search(r"자격|면허|보유|취득|소지|수료|이수|합격", text):
            return held
        compact = re.sub(r"\s+", "", text)
        for pat, name in L.TEXT_DETECT:
            if re.search(pat, text) and name not in held:
                held.append(name)
        for n in self.lic_names:
            if len(n) >= 4 and n in compact and n not in held and not any(n in h for h in held):
                held.append(n)
        return held

    def _user_vectors(self, card):
        n = len(self.kw_list)
        match, ev, act = np.zeros(n), np.zeros(n), np.zeros(n)
        for kw, f in card["keywords"].items():
            j = self.kw_idx[kw]
            match[j] = max(match[j], f["match_weight"])
            ev[j] = max(ev[j], f["evidence_strength"] * card["context_weight"])
            if self.cat[kw] in ACTION_CATS:
                act[j] = max(act[j], f["match_weight"] * self.disc[kw])
        rel = np.zeros(n)
        for kw, f in card["keywords"].items():
            for k2, w in self.related.get(kw, []):
                j = self.kw_idx[k2]
                rel[j] = max(rel[j], f["match_weight"] * w)
        return match, ev, act, rel

    def score(self, card):
        match, ev, act, rel = self._user_vectors(card)
        eff = np.maximum(match, rel * 0.8)
        Wt = self.W * self.topmask
        kscore = (Wt * eff).sum(axis=1) / self.k_denom

        sem_raw = (self.D @ self.vec.transform([card["text"]]).T).toarray().ravel()
        sem = np.clip(sem_raw / SEM_SCALE, 0, 1)
        name_hit = np.array([len(n) >= 3 and n in card["text"] for n in self.base_names])
        sem = np.where(name_hit, np.maximum(sem, 0.9), sem)

        n_occ = len(self.occ_ids)
        num = np.zeros(n_occ)
        for kw in card["keywords"]:
            j = self.kw_idx[kw]
            if act[j] == 0:
                continue
            link = self.IMPN[:, j].copy()
            for k2, w in self.related.get(kw, []):
                link = np.maximum(link, 0.8 * w * self.IMPN[:, self.kw_idx[k2]])
            num += act[j] * link
        ascore = np.clip(num / act.sum(), 0, 1) if act.sum() > 0 else np.zeros(n_occ)

        hit = (self.W > 0) & ((match > 0) | (rel > 0))[None, :]
        wsum = (self.W * hit).sum(axis=1) + 1e-9
        escore = (self.W * hit * ev[None, :]).sum(axis=1) / wsum * np.clip(kscore / 0.3, 0, 1)
        if card["achievements"]:
            escore = np.clip(escore * 1.1, 0, 1)

        qscore, qnotes = self._qualification(card)
        final = 100 * (WEIGHTS["keyword"] * kscore + WEIGHTS["semantic"] * sem + WEIGHTS["action"] * ascore +
                       WEIGHTS["experience"] * escore + WEIGHTS["qualification"] * qscore)
        experienced = card["context"] == "인턴·직무 경력"
        penalty = np.ones(len(self.occ_ids))
        if not experienced:
            penalty = np.where(self.senior, penalty * 0.85, penalty)
            penalty = np.where(self.career_share >= 0.6, penalty * 0.92, penalty)
        final = final * penalty * self.reliability
        core_hits = ((self.W > 0) & (match > 0)[None, :] & ~np.isin(np.array(self.kw_list), list(self.common))[None, :]).sum(axis=1)
        lic_hit = np.array([bool(qnotes[o]["held_related"]) for o in self.occ_ids])
        eligible = ((kscore >= 0.12) | (ascore >= 0.25) | lic_hit) & ((core_hits >= 1) | lic_hit)
        return pd.DataFrame(dict(occupation_id=self.occ_ids, final=final.round(2), penalty=penalty.round(3), career_share=self.career_share.round(3), keyword=kscore.round(3), semantic=sem.round(3),
                                 action=ascore.round(3), experience=escore.round(3), qualification=qscore.round(3),
                                 core_hits=core_hits, eligible=eligible, family=self.fam)), qnotes

    def _qualification(self, card):
        held = set(card["licenses"])
        held |= {p for h in held for p in [L.parent_name(h)] if p}
        if any(h.startswith("자동차운전면허") for h in held):
            held.add("자동차운전면허")
        user_kws = set(card["keywords"])
        scores, notes = [], {}
        pref = self.opref[self.opref.use_in_matching]
        pref_by = pref.groupby("occupation_id")["preference_name"].apply(set).to_dict()
        legal_by = self.legal.groupby("occupation_id")
        legal_map = {o: g for o, g in legal_by}
        prac_map = {o: set(g.license_name) for o, g in self.practice.groupby("occupation_id")}
        rel_lic = self.olic.groupby("occupation_id")["license_name"].apply(set).to_dict()
        for o in self.occ_ids:
            note = dict(legal_required=[], legal_conditional=[], missing_legal=[], held_related=[], practice_required=[], pref_met=[])
            s, cap = 0.5, 1.0
            g = legal_map.get(o)
            if g is not None:
                for lid, gg in g.groupby("legal_id"):
                    names = set(gg.license_name)
                    typ = gg.requirement_type.iloc[0]
                    label = " 또는 ".join(sorted(names, key=len)[:3])
                    (note["legal_required"] if typ == "필수(법정)" else note["legal_conditional"]).append(dict(license=label, law=gg.legal_basis.iloc[0],
                                                                                                        condition=gg.legal_condition.iloc[0], status=gg.verification_status.iloc[0]))
                    if names & held:
                        s = max(s, 1.0)
                    else:
                        note["missing_legal"].append(dict(license=label, type=typ))
                        cap = min(cap, 0.2 if typ == "필수(법정)" else 0.4)
            pr = prac_map.get(o, set())
            note["practice_required"] = sorted(pr)[:5]
            if pr & held:
                s = max(s, 0.9)
            hr = rel_lic.get(o, set()) & held
            note["held_related"] = sorted(hr)
            if hr:
                s = max(s, 0.8)
            ps = pref_by.get(o, set())
            met = []
            if ("운전 가능(운전면허 소지)" in ps or "운전 경력" in ps) and any(h.startswith("자동차운전면허") for h in held):
                met.append("운전 가능(운전면허 소지)")
            if "SNS 운영 경험" in ps and "SNS 운영" in user_kws:
                met.append("SNS 운영 경험")
            if "Python 활용 경험" in ps and "Python" in user_kws:
                met.append("Python 활용 경험")
            if "SQL 활용 경험" in ps and "SQL" in user_kws:
                met.append("SQL 활용 경험")
            if "데이터 분석 프로젝트 경험" in ps and "데이터 분석" in user_kws:
                met.append("데이터 분석 프로젝트 경험")
            if "콘텐츠 제작 경험" in ps and "콘텐츠 제작" in user_kws:
                met.append("콘텐츠 제작 경험")
            if ("관련 전공·학력" in ps or "통계 관련 전공" in ps) and card["majors"]:
                met.append("전공 정보 있음(관련성은 직접 확인 필요)")
            note["pref_met"] = met
            s = min(1.0, s + 0.1 * len(met), cap + 0.1 * len(met))
            scores.append(s)
            notes[o] = note
        return np.array(scores), notes

    def recommend(self, text, top_n=5, n_more=5, diversity=0.35, per_family=2):
        card = self.extract(text)
        sc, qnotes = self.score(card)
        top = sc.loc[sc.eligible, "final"].max() if sc.eligible.any() else 0
        cut = max(MIN_SCORE, REL_CUT * top)
        pool = sc[sc.eligible & (sc.final >= MIN_SCORE)].sort_values("final", ascending=False).head(60).to_dict("records")
        low_confidence = False
        if not pool or top < MIN_SCORE:
            el = sc[sc.eligible].copy()
            if card["context"] != "인턴·직무 경력":
                el = el[~self.senior[el.index]] if (~self.senior[el.index]).any() else el
            el = el.sort_values("final", ascending=False).drop_duplicates("family")
            pool = el.head(3).to_dict("records")
            low_confidence = True
            top_n, n_more = min(3, len(pool)), 0
        picked, fam_count = [], defaultdict(int)
        while pool and len(picked) < top_n + n_more:
            best, best_v = None, -1
            for c in pool:
                if fam_count[c["family"]] >= per_family:
                    continue
                if len(picked) < top_n and c["final"] < cut and not low_confidence:
                    continue
                i = self.occ_idx[c["occupation_id"]]
                sim = 0.0
                for p in picked:
                    j = self.occ_idx[p["occupation_id"]]
                    a, b = self.top_sets[i], self.top_sets[j]
                    sim = max(sim, 0.6 * len(a & b) / max(1, len(a | b)) + 0.4 * (self.fam[i] == self.fam[j]))
                v = c["final"] * (1 - diversity * sim)
                if v > best_v:
                    best, best_v = c, v
            if best is None:
                if len(picked) < top_n:
                    top_n = len(picked)
                    continue
                break
            best["mmr"] = round(best_v, 2)
            picked.append(best)
            fam_count[best["family"]] += 1
            pool.remove(best)
        main = sorted(picked[:top_n], key=lambda x: -x["final"])
        extra = sorted(picked[top_n:], key=lambda x: -x["final"])
        results = [self._explain(card, p, qnotes[p["occupation_id"]]) for p in main]
        names = dict(zip(self.occ.occupation_id, self.occ.occupation_name))
        more = [dict(occupation_id=p["occupation_id"], occupation_name=names[p["occupation_id"]], final=p["final"]) for p in extra]
        return dict(experience_card=self._card_view(card), recommendations=results, more_candidates=more, low_confidence=low_confidence, ranking_table=sc)

    def _card_view(self, card):
        kws = sorted(card["keywords"].values(), key=lambda x: -x["match_weight"])
        return dict(context=card["context"], activities=card["activities"], actions=card["actions"],
                    achievements=[a["text"] + (f" ({a['change_pct']:+}%)" if "change_pct" in a else "") for a in card["achievements"]],
                    competencies=[f"{k['keyword']}({k['match_type']})" for k in kws], licenses=card["licenses"], majors=card["majors"])

    def _explain(self, card, row, qn):
        oid = row["occupation_id"]
        o = self.occ.set_index("occupation_id").loc[oid]
        p = self.prof[self.prof.occupation_id == oid].copy()
        p["w"] = p.apply(lambda r: IMP_W[r.importance] * r.combined_score, axis=1)
        user = set(card["keywords"])
        matched = p[p.keyword.isin(user)].sort_values("w", ascending=False)
        related = []
        for kw in user:
            for k2, w in self.related.get(kw, []):
                if k2 in set(p.keyword) and k2 not in user:
                    related.append(f"{kw}→{k2}")
        gaps = p[(~p.keyword.isin(user)) & p.importance.isin(["required", "major"])].sort_values("w", ascending=False)
        gaps = [g for g in gaps.keyword if not any(g == r.split("→")[1] for r in related)][:6]
        cautions = []
        if row["penalty"] < 1:
            cautions.append("경력직 위주 직무일 수 있음(관리직이거나 공고의 경력 요구 비율이 높음)")
        if qn["missing_legal"]:
            cautions += [f"{m['license']} 필요({m['type']})" for m in qn["missing_legal"]]
        return dict(occupation_id=oid, occupation_name=o.occupation_name, job_family=o.job_family_name, category=o.category,
                    score=row["final"], cautions=cautions, score_breakdown={k: row[k] for k in ["keyword", "semantic", "action", "experience", "qualification"]},
                    matched_competencies=list(matched.keyword[:8]), transferable_links=related[:6], competency_gaps=gaps,
                    legal_required=qn["legal_required"], legal_conditional=qn["legal_conditional"], missing_legal=qn["missing_legal"],
                    practice_required_licenses=qn["practice_required"], held_related_licenses=qn["held_related"], preferences_met=qn["pref_met"],
                    market_open_postings=int(o.open_posting_count), postings=self.postings_for(oid, user))

    def postings_for(self, oid, user_kws, n=3):
        ps = self.posts[(self.posts.occupation_id == oid) & ~self.posts.is_exact_duplicate & self.posts.is_open_as_of_run]
        if ps.empty:
            return []
        kw = self.pkw[self.pkw.posting_id.isin(ps.posting_id) & self.pkw.keyword.isin(user_kws)]
        ov = kw.groupby("posting_id")["keyword"].apply(lambda s: sum(self.disc[k] for k in s))
        ps = ps.assign(overlap=ps.posting_id.map(ov).fillna(0),
                       newbie=ps["경력"].isin(["신입", "관계없음"]).astype(float),
                       fresh=(ps.reg_date - ps.reg_date.min()).dt.days / max(1, (ps.reg_date.max() - ps.reg_date.min()).days or 1))
        ps["rank_score"] = ps.overlap + 0.3 * ps.newbie + 0.2 * ps.fresh
        ps = ps.sort_values(["rank_score", "deadline"], ascending=[False, False]).head(n)
        return [dict(posting_id=r.posting_id, company=r.기업명, title=r.채용제목, region=r.근무지역, career=r.경력, education=r.최소학력,
                     wage=r.임금조건, deadline=str(r.deadline.date()), d_day=int((r.deadline - TODAY).days), matched_keywords=round(r.overlap, 2))
                for r in ps.itertuples()]
