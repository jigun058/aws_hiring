import { useEffect, useState } from 'react'
import {
  NO_FILTERS, TYPE_LABEL, askSlot, editField, fmt, focusChat, pickJob, pickPost, removeComp, saveCard, selectedPost, set, setFilters, undoRemove,
} from './store'
import { AiDot, Btn, GRADE, Grade, H1, Pill, Spinner, won } from './ui'

// ---------------- ① 경험 수집 ----------------
const START_TYPES = [['job', '직장 경력'], ['part_time', '아르바이트·단기 일'], ['certificate', '자격증·교육']]
const CARE_TYPES = [['family_care', '가족 돌봄'], ['community', '지역 활동']]

export function Step1({ s }) {
  const toggle = t => set(p => ({ types: p.types.includes(t) ? p.types.filter(x => x !== t) : [...p.types, t] }))
  const chosen = [...START_TYPES, ...(s.care ? CARE_TYPES : [])].filter(([t]) => s.types.includes(t) || (s.care && CARE_TYPES.some(c => c[0] === t)))
  const startChat = () => {
    const names = chosen.map(c => c[1])
    if (names.length) set(p => ({ msgs: [...p.msgs, { id: `t${Date.now()}`, r: 'a', step: 1,
      t: `${names.join(', ')} 순서로 여쭤볼게요.\n먼저 ${names[0]}부터 들려주세요. 어디서, 얼마나, 어떤 일을 하셨나요?` }] }))
    focusChat()
  }
  return (
    <div className="flex flex-col gap-10">
      <H1 title="지금까지 해 오신 일을 모아 볼게요" sub="오른쪽 대화창에 해 오신 일을 들려주세요. AI 도우미가 경험마다 카드를 만들고, 빈 곳을 하나씩 여쭤봐요." />
      <div className="grid grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)] gap-5">
        <div className="border border-line rounded-[20px] px-8 py-8 flex flex-col gap-3">
          <span className="text-[16px] font-bold text-ok">✓ 이력서가 없어도 괜찮아요</span>
          <div className="text-[23px] font-extrabold text-ink leading-[1.4]">대화만으로 시작할 수 있어요</div>
          <p className="m-0 text-[17px] text-sub leading-[1.65]">“마트에서 8년 동안 재고 관리를 했어요”처럼 한두 문장이면 돼요. 대답이 어려우면 예시 답을 누르기만 하세요.</p>
          <Btn size="lg" className="mt-auto self-start" onClick={startChat}>대화창에서 시작하기 →</Btn>
        </div>
        <div className="border-[1.5px] border-dashed border-field rounded-[20px] px-7 py-8 flex flex-col items-center justify-center text-center gap-2.5">
          <div className="size-14 rounded-full border-[1.5px] border-field flex items-center justify-center text-[26px] font-extrabold text-muted">↑</div>
          <div className="text-[20px] font-extrabold text-muted">이력서 파일 올리기</div>
          <div className="text-[16px] text-muted leading-[1.6]">준비 중이에요. 지금은 대화로 시작해 주세요.</div>
        </div>
      </div>

      <div className="flex flex-col gap-3.5">
        <div>
          <h2 className="m-0 mb-1 text-[24px] font-extrabold text-ink">어떤 경험을 정리할까요?</h2>
          <p className="m-0 text-[17px] text-sub">골라 주시면 그 순서대로 여쭤볼게요. 나중에 바꿀 수 있어요.</p>
        </div>
        <div className="flex flex-wrap gap-2.5">
          {START_TYPES.map(([t, label]) => <Pill key={t} on={s.types.includes(t)} onClick={() => toggle(t)} className="h-[50px] px-[22px] text-[18px]">{s.types.includes(t) ? '✓ ' : ''}{label}</Pill>)}
        </div>
        <div className="flex items-center gap-5 justify-between flex-wrap pt-4 mt-1 border-t border-line2">
          <span className="flex-1 min-w-[280px] text-[17px] text-sub">원하시면 가족 돌봄·지역 활동도 경험으로 넣을 수 있어요. 넣고 싶을 때만 골라 주세요.</span>
          {s.care
            ? <button onClick={() => set({ care: false })} className="h-[44px] px-[18px] rounded-full border-2 border-brand bg-white text-brand text-[16px] font-bold">✓ 넣었어요 · 빼기</button>
            : <button onClick={() => set({ care: true })} className="h-[44px] px-[18px] rounded-full border border-dashed border-faint bg-white text-sub text-[16px] hover:border-brand hover:text-brand">+ 가족 돌봄·지역 활동 넣기</button>}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="m-0 text-[24px] font-extrabold text-ink">모은 경험 {s.cards.length}개</h2>
        <div className="border-t-2 border-ink">
          {s.cards.length ? s.cards.map(c => (
            <div key={c.id} className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 items-center px-1 py-4 border-b border-line">
              <div className="min-w-0">
                <div className="text-[15px] font-bold text-accent">{TYPE_LABEL[c.card.type]}</div>
                <div className="text-[19px] font-extrabold text-ink truncate">{c.card.activity}</div>
                <div className="text-[16px] text-sub">찾은 역량 {c.competencies.length}개{c.competencies.length ? ` · ${c.competencies.slice(0, 3).map(k => k.keyword).join(', ')}` : ''}</div>
              </div>
              {c.question && !c.question.end
                ? <span className="text-[16px] font-bold text-brand">{s.activeCard === c.id ? '대화창에서 묻는 중' : '여쭤볼 것이 남았어요'}</span>
                : <span className="text-[16px] font-bold text-ok">✓ 정리했어요</span>}
            </div>
          )) : <div className="py-8 text-center text-[17px] text-sub">아직 모은 경험이 없어요. 대화창에 첫 경험을 적어 주세요.</div>}
        </div>
      </div>
    </div>
  )
}

// ---------------- ② 경험 카드 ----------------
const LONG = [['purpose', '목적 · 무엇을 위한 일이었나요'], ['role', '역할 · 어떤 자리에서 일했나요'], ['actions', '행동 · 실제로 한 일 (한 줄에 하나)'], ['results', '성과 · 나아진 점 (한 줄에 하나)']]
const ASK_ME = new Set(['missing', 'vague', 'unknown_by_user', 'skipped'])
const slotText = v => Array.isArray(v) ? v.map(x => x.value).join('\n') : v?.value || ''
const missingCount = c => c.card.type === 'certificate' ? 0
  : ['purpose', 'role', 'actions', 'results'].filter(k => ASK_ME.has(c.card.slot_status[k]) && !slotText(c.card.slots[k])).length

function Field({ c, f, label, long }) {
  const orig = f === 'activity' ? c.card.activity : slotText(c.card.slots[f])
  const [v, setV] = useState(orig)
  const [writing, setWriting] = useState(false)
  useEffect(() => { setV(orig); setWriting(false) }, [orig, c.id])
  const commit = () => { if (v.trim() !== orig.trim()) editField(c.id, f, v) }
  const st = c.card.slot_status[f]
  const ask = long && c.card.type !== 'certificate' && ASK_ME.has(st) && !orig && !writing
  return (
    <label className="flex-1 flex flex-col gap-2 min-w-0">
      <span className="text-[15px] font-bold text-sub">{label}</span>
      {ask ? (
        <div className="flex items-center gap-3 flex-wrap px-4 py-3.5 rounded-lg border-[1.5px] border-dashed border-[#D9A24A] bg-white">
          <span className="flex-1 min-w-[220px] text-[17px] text-warn"><b>더 알려 주세요.</b> 아직 이 칸이 비어 있어요. 작은 일이라도 괜찮아요.</span>
          <Btn onClick={e => { e.preventDefault(); askSlot(c.id, f) }}>대화창에서 알려 주기</Btn>
          <Btn kind="outline" onClick={e => { e.preventDefault(); setWriting(true) }}>직접 적기</Btn>
        </div>
      ) : long ? (
        <textarea value={v} onChange={e => setV(e.target.value)} onBlur={commit} rows={Math.max(2, v.split('\n').length)} autoFocus={writing}
          className="field px-3.5 py-3 text-[18px] leading-[1.6] resize-y" />
      ) : (
        <input value={v} onChange={e => setV(e.target.value)} onBlur={commit} onKeyDown={e => e.key === 'Enter' && e.currentTarget.blur()}
          className="field h-[52px] px-3.5 text-[18px] min-w-0" />
      )}
      {long && st === 'vague' && orig && <span className="text-[15px] text-warn">조금 더 구체적으로 적어 주시면 역량을 더 정확히 찾을 수 있어요.</span>}
    </label>
  )
}

export function Step2({ s }) {
  const i = Math.min(s.cardSel, s.cards.length - 1), c = s.cards[i]
  const [open, setOpen] = useState({})
  const comps = c.competencies.filter(k => !c.removed.includes(k.kw_idx))
  return (
    <div className="flex flex-col gap-7">
      <H1 title="경험 카드 초안을 확인해 주세요" sub="AI 도우미가 대화를 보고 만든 초안이에요. 틀린 곳은 바로 고치고, 맞으면 저장해 주세요." />
      <div className="grid grid-cols-[200px_minmax(0,1fr)] xl:grid-cols-[minmax(220px,270px)_minmax(0,1fr)] gap-5 xl:gap-7 items-start">
        <div className="flex flex-col gap-2 sticky top-0">
          <div className="text-[16px] font-bold text-sub pb-1">카드 초안 {s.cards.length}장</div>
          {s.cards.map((x, k) => {
            const miss = missingCount(x)
            return (
              <button key={x.id} onClick={() => set({ cardSel: k })}
                className={`text-left p-4 rounded-xl bg-white flex flex-col gap-1.5 hover:border-brand border ${k === i ? 'border-brand shadow-[inset_0_0_0_1px_#12307A]' : 'border-line'}`}>
                <span className="text-[14px] font-bold text-accent">{TYPE_LABEL[x.card.type]}</span>
                <span className="text-[18px] font-extrabold text-ink leading-[1.4]">{x.card.activity}</span>
                {x.card.slots.period?.value && <span className="text-[15px] text-sub">{x.card.slots.period.value}</span>}
                <div className="flex flex-wrap gap-x-3.5 gap-y-1 mt-2 text-[14px] font-bold">
                  {x.saved ? <span className="text-ok">✓ 저장함</span> : <span className="text-sub">저장 전</span>}
                  {miss > 0 && <span className="text-warn">더 알려 주세요 - {miss}곳</span>}
                </div>
              </button>
            )
          })}
        </div>
        <div className="border border-line rounded-[20px] p-6 xl:p-9 flex flex-col gap-9 shadow-[0_2px_8px_rgba(14,35,80,.05)]">
          <div className="flex items-center gap-4 text-[15px] font-bold">
            <span className="text-sub">카드 {i + 1} / {s.cards.length}</span>
            <span className="inline-flex items-center gap-1.5 text-ai"><AiDot size={9} />초안</span>
            <span className="flex-1" />
            {c.saved && <span className="text-ok text-[16px]">✓ 내 경험에 저장했어요</span>}
          </div>
          <div className="grid grid-cols-2 2xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1.2fr)] gap-5">
            <div className="col-span-2 2xl:col-span-1 flex"><Field c={c} f="activity" label="활동명" /></div>
            <label className="flex flex-col gap-2 min-w-0">
              <span className="text-[15px] font-bold text-sub">유형</span>
              <select value={c.card.type} onChange={e => editField(c.id, 'type', e.target.value)} className="field h-[52px] px-3 text-[18px] min-w-0">
                {Object.entries(TYPE_LABEL).map(([t, l]) => <option key={t} value={t}>{l}</option>)}
              </select>
            </label>
            <Field c={c} f="period" label="기간" />
          </div>
          <div className="flex flex-col gap-7">
            {LONG.filter(([f]) => c.card.slot_status[f] !== 'not_asked' || slotText(c.card.slots[f])).map(([f, label]) => <Field key={f} c={c} f={f} label={label} long />)}
          </div>
          <div className="flex flex-col gap-3 pt-8 border-t border-line2">
            <div className="flex items-baseline justify-between gap-3 flex-wrap">
              <h3 className="m-0 text-[22px] font-extrabold text-ink">찾은 역량 {comps.length}개</h3>
              {c.removed.length > 0 && <button onClick={() => undoRemove(c.id)} className="border-0 bg-transparent text-brand text-[16px] font-bold underline underline-offset-4">지운 역량 {c.removed.length}개 되돌리기</button>}
            </div>
            <div className="text-[17px] font-bold text-ai">경험 글에서 역량 사전과 맞춰 찾은 역량이에요. 맞지 않으면 지워 주세요.</div>
            <div className="grid grid-cols-[auto_1fr] gap-x-5 gap-y-1.5 text-[15px] text-sub pb-2">
              {['L3', 'L2', 'L1'].flatMap(g => [<b key={g} className={GRADE[g][1]}>{GRADE[g][0]}</b>, <span key={g + 'd'}>{GRADE[g][2]}</span>])}
            </div>
            <div className="border-t border-line">
              {comps.length ? comps.map(k => (
                <div key={k.kw_idx} className="py-5 border-b border-line flex flex-col gap-2.5">
                  <div className="flex items-center gap-4">
                    <div className="flex-1 min-w-0 flex items-baseline gap-x-3.5 gap-y-1 flex-wrap">
                      <span className="text-[19px] font-extrabold text-ink">{k.keyword}</span><Grade lv={k.level} />
                    </div>
                    <div className="shrink-0 flex gap-2">
                      <Btn kind={open[k.kw_idx] ? 'outline' : 'plain'} size="sm" className={open[k.kw_idx] ? '' : 'text-brand'} onClick={() => setOpen(o => ({ ...o, [k.kw_idx]: !o[k.kw_idx] }))}>{open[k.kw_idx] ? '근거 접기 ▴' : '근거 보기 ▾'}</Btn>
                      <Btn kind="plain" size="sm" className="text-sub hover:border-err hover:text-err" onClick={() => removeComp(c.id, k.kw_idx)}>지우기</Btn>
                    </div>
                  </div>
                  {open[k.kw_idx] && <span className="text-[17px] text-ink leading-[1.6]">“{k.quote}”</span>}
                </div>
              )) : <div className="py-6 text-[17px] text-sub">아직 찾은 역량이 없어요. 행동·성과 칸에 하신 일을 적어 주시면 다시 찾아요.</div>}
            </div>
          </div>
          <div className="flex gap-3 flex-wrap justify-center pt-2">
            {c.saved
              ? <Btn size="lg" onClick={() => set({ cardSel: (i + 1) % s.cards.length })} disabled={s.cards.length < 2}>저장했어요 · 다음 카드 보기</Btn>
              : <Btn size="lg" onClick={() => saveCard(c.id)}>이 카드 저장하기</Btn>}
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------- ③ 직무 추천 ----------------
const PARTS = {
  keyword: ['키워드 일치', '공고에 자주 나오는 말과 내 경험의 말이 겹치는 정도'],
  semantic: ['의미 유사', '말은 달라도 뜻이 비슷한 정도'],
  action: ['업무 행동 연관', '해 본 일과 이 직무가 하는 일이 닮은 정도'],
  experience: ['성과·경험 수준', '성과가 얼마나 확실한지, 어떤 경험이었는지'],
  qualification: ['자격·우대', '자격증과 우대 조건을 채운 정도'],
}

export function Step3({ s }) {
  const J = s.jobs[s.jobSel] || s.jobs[0]
  const reason = s.reasons[J.occupation_id]
  return (
    <div className="flex flex-col gap-7">
      <H1 title={`내 경험에 맞는 직무 ${s.jobs.length}가지`}
        sub={<>저장한 경험 카드를 직무 정보 {s.meta ? fmt(s.meta.occupations) + '개' : ''}와 비교했어요. 점수는 100점 만점의 <b className="text-body">경험 일치도</b>이고, 합격 가능성은 아니에요.</>} />
      <div className="grid grid-cols-3 gap-4">
        {s.jobs.map((j, k) => (
          <button key={j.occupation_id} onClick={() => pickJob(k)} aria-pressed={k === s.jobSel}
            className={`text-left p-[22px] rounded-2xl bg-white flex flex-col gap-2.5 border hover:border-brand ${k === s.jobSel ? 'border-brand shadow-[inset_0_0_0_1px_#12307A]' : 'border-line'}`}>
            <span className="text-[16px] font-extrabold text-accent">{k + 1}위</span>
            <span className="text-[21px] font-extrabold text-ink leading-[1.35]">{j.name}</span>
            <span className="flex items-baseline gap-1"><span className="text-[34px] xl:text-[42px] font-extrabold text-brand leading-none">{j.score.toFixed(1)}</span><span className="text-[17px] text-sub">점 / 100</span></span>
            <div className="h-1 rounded-sm bg-line2 overflow-hidden"><div className="h-full bg-brand" style={{ width: `${j.score}%` }} /></div>
            <span className="text-[16px] text-sub leading-[1.55]">{j.family ? `${j.family} · ` : ''}공고 {fmt(j.open_postings)}건</span>
          </button>
        ))}
      </div>
      <div className="border border-line rounded-[20px] p-8 flex flex-col gap-7">
        <div className="flex items-end justify-between gap-4 flex-wrap pb-6 border-b border-line2">
          <div><div className="text-[16px] font-bold text-accent">{s.jobSel + 1}위 직무 자세히 보기</div><h2 className="mt-1 mb-0 text-[28px] font-extrabold text-ink">{J.name}</h2></div>
          <div className="text-[18px] text-sub">경험 일치도 <b className="text-[28px] text-brand">{J.score.toFixed(1)}점</b> · 공고 {fmt(J.open_postings)}건</div>
        </div>
        <div className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] gap-10">
          <div className="flex flex-col gap-[18px]">
            <h3 className="m-0 text-[20px] font-extrabold text-ink">점수는 이렇게 나왔어요</h3>
            {Object.entries(J.parts).map(([k, p]) => (
              <div key={k} className="flex flex-col gap-1.5">
                <div className="flex justify-between gap-3 items-baseline"><span className="text-[18px] font-bold text-ink">{PARTS[k]?.[0] || k}</span>
                  <span className="text-[17px] text-sub shrink-0"><b className="text-ink text-[19px]">{(p.value * p.max).toFixed(1)}</b> / {p.max}</span></div>
                <div className="h-1.5 rounded-sm bg-line2 overflow-hidden"><div className="h-full bg-brand" style={{ width: `${p.value * 100}%` }} /></div>
                <span className="text-[15px] text-sub">{PARTS[k]?.[1]}</span>
              </div>
            ))}
            {J.cautions.map(t => <p key={t} className="m-0 text-[15px] text-warn">{t}</p>)}
          </div>
          <div className="flex flex-col gap-6">
            <div>
              <h3 className="m-0 mb-1.5 text-[20px] font-extrabold text-ink">근거가 된 내 역량</h3>
              {J.evidence.map(e => (
                <div key={e.keyword} className="flex items-center gap-2.5 py-3 border-b border-line2">
                  <span className="flex-1 min-w-0 text-[17px] font-bold text-ink">{e.keyword}
                    <span className="block text-[14px] font-normal text-sub">{e.card ? `${e.card} 카드` : '경험 글에서 찾음'}</span></span>
                  <Grade lv={e.level} />
                </div>
              ))}
            </div>
            {(J.gaps.length > 0 || J.missing_legal.length > 0) && (
              <div className="flex flex-col gap-1.5">
                <span className="text-[18px] font-extrabold text-ink">더 채우면 좋은 역량</span>
                <span className="text-[17px] text-sub">{[...J.missing_legal.map(x => `${x}(법정 자격)`), ...J.gaps].join(' · ')}</span>
              </div>
            )}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2"><AiDot /><span className="text-[18px] font-extrabold text-ink">{reason?.by === 'rule' ? '추천 이유' : 'AI가 쓴 추천 이유'}</span></div>
              {!reason || reason.loading ? <span className="flex items-center gap-2.5 text-[17px] text-sub"><Spinner size={18} w={2} />추천 이유를 쓰는 중이에요…</span>
                : reason.error ? <span className="text-[17px] text-sub">추천 이유를 불러오지 못했어요. <button className="border-0 bg-transparent text-brand font-bold underline" onClick={() => pickJob(s.jobSel)}>다시 시도</button></span>
                  : <p className="m-0 text-[17px] leading-[1.75] text-body text-pretty">{reason.reason}</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------- ④ 채용공고 ----------------
const dday = p => p.d_day === null ? (p.until_hired ? '채용 시까지' : '마감일 없음') : `D-${p.d_day}`
const ddColor = p => p.d_day !== null && p.d_day <= 7 ? 'text-err' : 'text-ink'
const DEAD = [['전체', null], ['7일 이내', 7], ['한 달 이내', 31]]
const HOURS = [['전체', ''], ['전일제', '전일제'], ['시간제', '시간제']]

export function Step4({ s }) {
  const J = s.jobs[s.jobSel], f = s.filters, P = selectedPost(s), date = s.meta?.data_date || '2026-11-12'
  const [tip, setTip] = useState(null)
  const [m, d] = date.split('-').slice(1).map(Number)
  return (
    <div className="flex flex-col gap-8">
      <H1 title={`${J.name} 채용공고`} sub={`서울시 일자리포털에 ${m}월 ${d}일 기준으로 올라온 서울·경기·인천 공고예요. 마감일(D-day)도 그날 기준이에요.`} />
      <div className="flex flex-wrap items-end gap-7 pb-6 border-b border-line">
        <label className="flex flex-col gap-2">
          <span className="text-[15px] font-bold text-sub">시·도</span>
          <select value={f.sido} onChange={e => setFilters({ sido: e.target.value, sigungu: '' })} className="field h-[48px] min-w-[120px] px-3.5 text-[17px]">
            <option value="">전체</option>{(s.meta?.sido || []).map(x => <option key={x}>{x}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-[15px] font-bold text-sub">시·군·구</span>
          <select value={f.sigungu} disabled={!f.sido} onChange={e => setFilters({ sigungu: e.target.value })} className="field h-[48px] min-w-[150px] px-3.5 text-[17px] disabled:bg-soft disabled:text-muted">
            <option value="">{f.sido ? '전체' : '시·도를 먼저'}</option>{(s.meta?.sigungu?.[f.sido] || []).map(x => <option key={x}>{x}</option>)}
          </select>
        </label>
        <div className="flex flex-col gap-2"><span className="text-[15px] font-bold text-sub">근무시간</span>
          <div className="flex gap-1.5">{HOURS.map(([l, v]) => <Pill key={l} on={f.hours === v} onClick={() => setFilters({ hours: v })}>{l}</Pill>)}</div></div>
        <div className="flex flex-col gap-2"><span className="text-[15px] font-bold text-sub">마감일 ({m}월 {d}일 기준)</span>
          <div className="flex gap-1.5">{DEAD.map(([l, v]) => <Pill key={l} on={f.deadline_days === v} onClick={() => setFilters({ deadline_days: v })}>{l}</Pill>)}</div></div>
        <span className="flex-1" />
        <div className="flex items-center gap-3">
          {s.postsLoading && <Spinner size={20} w={2} />}
          <span className="text-[17px] text-body whitespace-nowrap">총 <b>{fmt(s.posts.total)}</b>건</span>
          <Btn kind="plain" onClick={() => setFilters(NO_FILTERS)}>↺ 필터 초기화</Btn>
        </div>
      </div>

      {!s.posts.postings.length ? (
        <div className="py-14 px-6 text-center flex flex-col items-center gap-3">
          <div className="text-[22px] font-extrabold text-ink">조건에 맞는 공고가 없어요</div>
          <p className="m-0 text-[17px] text-sub">지역이나 근무시간 조건을 넓혀 보세요. 다른 추천 직무를 골라 보셔도 돼요.</p>
          <Btn size="lg" onClick={() => setFilters(NO_FILTERS)}>필터 초기화하기</Btn>
        </div>
      ) : (
        <div className={`grid grid-cols-[minmax(260px,340px)_minmax(0,1fr)] gap-7 items-start ${s.postsLoading ? 'opacity-60' : ''}`}>
          <div className="flex flex-col gap-3">
            {s.posts.total > s.posts.postings.length && <span className="text-[15px] text-sub">내 역량과 많이 겹치는 순서로 {s.posts.postings.length}건을 보여 드려요.</span>}
            {s.posts.postings.map(p => {
              const req = p.required, have = req.filter(x => x.has).length
              return (
                <button key={p.posting_id} onClick={() => pickPost(p.posting_id)} onMouseEnter={() => setTip(p.posting_id)} onMouseLeave={() => setTip(null)}
                  className={`relative text-left px-[22px] py-5 rounded-2xl bg-white flex flex-col border hover:border-brand ${p.posting_id === s.postSel ? 'border-brand shadow-[inset_0_0_0_1px_#12307A]' : 'border-line'}`}>
                  <span className="text-[15px] text-sub pr-6"><b className={ddColor(p)}>{dday(p)}</b> · {p.company}</span>
                  <span className="mt-2 text-[19px] font-extrabold text-ink leading-[1.4] pr-6">{p.title}</span>
                  <span className="mt-1 text-[15px] text-sub">{p.sido} {p.sigungu} · {p.part_time ? '시간제' : '전일제'}</span>
                  <div className="mt-4 pt-3.5 border-t border-line2 flex items-baseline justify-between gap-3">
                    <span className="text-[15px] text-sub">필수 역량 <b className="text-[17px] text-ink">{req.length ? `${have}/${req.length}` : '공고에 없음'}</b></span>
                    {p.needs_license.length > 0 && <span className="text-[15px] font-bold text-warn">자격 취득 후 지원</span>}
                  </div>
                  {p.thin && <>
                    <span aria-label="공고 정보가 부족해요" className="absolute top-4 right-4 size-[26px] rounded-full border-[1.5px] border-sub text-sub text-[15px] font-extrabold font-serif flex items-center justify-center">i</span>
                    {tip === p.posting_id && <span className="absolute top-[50px] right-3 z-[4] w-[250px] px-3.5 py-3 rounded-[10px] bg-ink text-white text-[15px] leading-[1.55] shadow-[0_8px_24px_rgba(14,35,80,.18)]"><b>공고 정보가 부족해요</b><br />하게 될 업무와 요구 조건이 적게 적혀 있어 역량을 정확히 맞추기 어려워요.</span>}
                  </>}
                </button>
              )
            })}
          </div>
          {P && <PostDetail p={P} date={`${m}월 ${d}일`} />}
        </div>
      )}
    </div>
  )
}

function PostDetail({ p, date }) {
  const conds = [['근무시간', p.work_hours], ['급여', p.wage], ['고용 형태', p.employment_type], ['경력', p.career], ['학력', p.education],
    ['근무지', `${p.sido} ${p.sigungu}`], ['마감', p.deadline ? `${p.deadline} (${date} 기준 D-${p.d_day})` : dday(p)]].filter(c => c[1])
  const legal = p.licenses.filter(l => l.legal_required)
  const groups = [['필수', [...p.required, ...legal.map(l => ({ keyword: l.name, has: l.has, law: !l.has }))]], ['우대', p.preferred], ['하게 될 업무', p.tasks]]
  return (
    <div className="border border-line rounded-[20px] p-6 xl:p-9 flex flex-col gap-10">
      <div className="flex flex-col gap-2.5">
        <span className="text-[16px] text-sub"><b className={ddColor(p)}>{dday(p)}</b> · {p.company} · {p.employment_type}</span>
        <h2 className="m-0 text-[24px] xl:text-[28px] font-extrabold text-ink leading-[1.35] break-words">{p.title}</h2>
        {p.needs_license.length > 0 && <p className="mt-2 mb-0 text-[17px] text-body leading-[1.65]"><b className="text-warn">자격 취득 후 지원 가능</b> · 법으로 정한 ‘{p.needs_license.join('’, ‘')}’ 자격이 꼭 있어야 해요. 다음 단계에서 자격 과정을 함께 찾아 드려요.</p>}
        {p.thin && <p className="mt-2 mb-0 text-[17px] text-sub leading-[1.65]"><b className="text-body">공고 정보가 부족해요</b> · 하게 될 업무와 요구 조건이 적게 적혀 있어요. 지원 전에 회사에 전화로 물어보시길 권해요.</p>}
      </div>
      <div className="flex flex-col gap-3.5">
        <h3 className="m-0 text-[21px] font-extrabold text-ink">근무 조건</h3>
        <div className="flex flex-col border-t border-ink">
          {conds.map(([k, v]) => (
            <div key={k} className="grid grid-cols-[80px_minmax(0,1fr)] gap-3 py-3.5 border-b border-line2 items-baseline">
              <span className="text-[15px] text-sub">{k}</span><span className="text-[17px] text-ink leading-[1.45] break-words">{v}</span>
            </div>
          ))}
        </div>
        {p.conditions.length > 0 && <div className="text-[15px] text-sub">공고에 적힌 조건 · {p.conditions.map(c => c.quote).join(' / ')}</div>}
      </div>
      <div className="flex flex-col gap-3.5">
        <div className="flex items-baseline justify-between gap-4">
          <h3 className="m-0 text-[21px] font-extrabold text-ink">필요한 역량</h3>
          <span className="text-[15px] text-sub">✓ 있어요 · ○ 아직 없어요</span>
        </div>
        <div className="flex flex-col border-t border-ink">
          {groups.map(([name, items]) => (
            <div key={name} className="grid grid-cols-[96px_minmax(0,1fr)] gap-4 py-5 border-b border-line2">
              <div className="flex flex-col gap-0.5"><span className="text-[18px] font-extrabold text-ink">{name}</span>
                {items.length > 0 && <span className="text-[15px] text-sub">{items.filter(x => x.has).length}/{items.length}</span>}</div>
              {!items.length ? <span className="text-[17px] text-muted">공고에 적혀 있지 않아요</span> : (
                <div className="grid grid-cols-1 2xl:grid-cols-2 gap-x-6 gap-y-3">
                  {items.map(it => (
                    <div key={it.keyword} className="flex items-baseline gap-2.5 text-[17px] leading-[1.5]">
                      {it.has ? <><span className="w-4 shrink-0 text-brand font-extrabold">✓</span><span className="text-ink font-bold">{it.keyword}</span></>
                        : <><span className="w-4 shrink-0 text-faint">○</span><span className="text-sub">{it.keyword}{it.law && <span className="block text-[15px] text-warn font-bold">법정 자격 · 취득 후 지원 가능</span>}</span></>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        {p.attitude.length > 0 && <div className="flex items-baseline gap-3 text-[15px] text-sub pt-1"><span className="shrink-0">태도 요구</span><span>{p.attitude.map(a => a.keyword).join(' · ')}</span></div>}
      </div>
    </div>
  )
}

// ---------------- ⑤ 교육과정 추천 ----------------
const WHY = {
  '법정 자격 필요': '법으로 정한 자격이라 있어야 지원할 수 있어요.',
  '필수 역량 부족': '고른 공고가 꼭 있어야 한다고 적은 역량이에요.',
  '우대 조건 부족': '고른 공고가 있으면 더 좋다고 적은 역량이에요.',
  '처음 해 보는 업무': '공고의 ‘하게 될 업무’에 적혀 있지만, 아직 해 보신 기록이 없어요.',
  '직무에서 자주 요구': '이 직무의 공고에서 자주 요구하는 역량이에요.',
}

export function Step5({ s }) {
  const P = selectedPost(s), J = s.jobs[s.jobSel]
  const withC = s.gaps.filter(g => g.courses.length)
  const nCourses = withC.reduce((a, g) => a + g.courses.length, 0)
  return (
    <div className="flex flex-col gap-8">
      <H1 title="부족한 역량을 채울 국비 교육과정" sub={`${P ? `${P.company} 공고` : `${J.name} 직무`} 기준이에요. 국민내일배움카드가 있으면 훈련비를 지원받을 수 있어요.`} />
      <div className="grid grid-cols-3 border border-line rounded-2xl">
        <div className="px-6 py-5"><div className="text-[15px] text-sub">부족한 역량</div><div className="text-[28px] font-extrabold text-ink">{s.gaps.length}개</div></div>
        <div className="px-6 py-5 border-l border-line"><div className="text-[15px] text-sub">교육으로 채울 수 있어요</div><div className="text-[28px] font-extrabold text-ink">{withC.length}개 · 과정 {nCourses}개</div></div>
        <div className="px-6 py-5 border-l border-line"><div className="text-[15px] text-sub">맞는 과정을 못 찾았어요</div><div className="text-[28px] font-extrabold text-ink">{s.gaps.length - withC.length}개</div></div>
      </div>
      {s.gaps.map((g, k) => (
        <section key={g.name} className="flex flex-col gap-[18px] pt-7 border-t-2 border-ink">
          <div className="flex items-start gap-3.5">
            <span className="size-8 rounded-full border-[1.5px] border-brand text-brand font-extrabold text-[16px] flex items-center justify-center shrink-0">{k + 1}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-5"><h2 className="m-0 flex-1 min-w-0 text-[23px] font-extrabold text-ink">{g.name}</h2><span className="shrink-0 text-[18px] font-bold text-warn">{g.label}</span></div>
              <p className="mt-1 mb-0 text-[17px] text-sub">{WHY[g.label]}</p>
            </div>
          </div>
          {g.courses.length ? g.courses.map(c => (
            <div key={c.course_id} className="grid grid-cols-[minmax(0,1fr)_auto] gap-5 items-center px-6 py-[22px] rounded-2xl border border-line shadow-[0_2px_8px_rgba(14,35,80,.05)]">
              <div className="flex flex-col gap-3 min-w-0">
                <div className="flex items-center gap-2 flex-wrap"><span className="text-brand text-[13px] font-bold">{c.type}</span><span className="text-[20px] font-extrabold text-ink">{c.name}</span></div>
                <div className="grid grid-cols-2 gap-x-6 gap-y-2">
                  {[['기관', c.institution], ['지역', c.region], ['기간', `${c.start} – ${c.end}`], ['훈련비', won(c.fee)]].map(([k2, v]) => (
                    <div key={k2}><div className="text-[14px] font-bold text-sub">{k2}</div><div className="text-[17px] text-ink">{v}</div></div>
                  ))}
                </div>
              </div>
              <div className="flex flex-col items-center gap-1.5">
                {c.url ? <a href={c.url} target="_blank" rel="noreferrer" className="h-[52px] px-[22px] rounded-full border-[1.5px] border-brand bg-white text-brand text-[17px] font-bold whitespace-nowrap no-underline flex items-center hover:bg-hover">신청 페이지 열기 ↗</a> : null}
                <span className="text-[14px] text-sub">고용24 누리집에서 열려요</span>
              </div>
            </div>
          )) : (
            <div className="px-6 py-5 rounded-2xl border border-line text-[17px] text-sub leading-[1.65]">
              지금 신청할 수 있는 국비 과정 가운데 이 역량에 맞는 과정을 찾지 못했어요.
            </div>
          )}
        </section>
      ))}
    </div>
  )
}
