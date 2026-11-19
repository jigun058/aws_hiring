import { useState } from 'react'
import { api } from './api'
import { STEPS, set, start, useApp } from './store'
import { AiDot, Btn, H1, Logo, Spinner } from './ui'

const STEP_DESC = ['대화로 해 오신 일을 모아요', 'AI가 만든 카드를 확인하고 고쳐요', '경험에 맞는 직무 3가지를 봐요', '실제 채용공고와 맞춰 봐요', '부족한 역량을 국비 교육으로 채워요']

export function Landing() {
  return (
    <div className="flex-1 overflow-y-auto bg-white">
      <div className="border-b border-line">
        <div className="max-w-[1200px] mx-auto px-12 h-20 flex items-center justify-between">
          <Logo />
          <Btn kind="outline" onClick={() => set({ screen: 'story' })} className="text-[17px]">재취업 이야기 읽어 보기</Btn>
        </div>
      </div>
      <div className="bg-[linear-gradient(180deg,#EAF5FD_0%,#FFFFFF_100%)]">
        <div className="max-w-[1200px] mx-auto px-12 pt-[88px] pb-14 text-center flex flex-col items-center gap-5">
          <span className="inline-flex items-center gap-2 text-[17px] font-bold text-accent"><AiDot size={9} />서울시 일자리포털 · 국비 교육과 함께 찾아요</span>
          <h1 className="m-0 text-[52px] leading-[1.3] font-extrabold text-ink tracking-[-0.02em] text-balance">지나온 경험 속에서<br />다시 할 수 있는 일을 찾아 드려요</h1>
          <p className="m-0 max-w-[720px] text-[21px] leading-[1.7] text-sub text-pretty">해 오신 일을 들려주시면 AI 도우미가 경험 카드로 정리하고, 맞는 직무와 채용공고, 부족한 부분을 채울 국비 교육과정까지 함께 찾아 드려요.</p>
        </div>
      </div>
      <div className="max-w-[1200px] mx-auto px-12 pb-20 flex flex-col gap-16">
        <div className="grid grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] gap-6">
          <button onClick={start} className="text-left border-[1.5px] border-brand bg-white rounded-[20px] px-10 py-9 flex flex-col gap-3.5 shadow-[0_8px_24px_rgba(14,35,80,.08)] hover:shadow-[0_12px_32px_rgba(14,35,80,.14)] text-inherit">
            <span className="text-[16px] font-bold text-accent">40~50대 · 경력이 끊겼던 분</span>
            <span className="text-[32px] font-extrabold text-ink leading-[1.3]">다시 일을 시작하려고 해요</span>
            <span className="text-[18px] text-sub leading-[1.7]">10년 전 직장 경력, 아르바이트, 자격증까지 모두 경험이에요. 하나씩 정리해서 지금 지원할 수 있는 일을 찾아 드려요.</span>
            <span className="mt-2.5 self-start inline-flex items-center gap-2.5 h-14 px-[30px] rounded-full bg-brand text-white text-[19px] font-bold">시작하기 →</span>
          </button>
          <div aria-disabled="true" className="border border-line bg-white rounded-[20px] px-10 py-9 flex flex-col gap-3.5 cursor-not-allowed">
            <span className="self-start text-sub text-[15px] font-bold">준비 중</span>
            <span className="text-[26px] font-extrabold text-muted leading-[1.3]">처음 일자리를 찾고 있어요</span>
            <span className="text-[17px] text-muted leading-[1.7]">대학생·취업준비생을 위한 화면을 준비하고 있어요. 수업, 동아리, 아르바이트 경험으로 시작하게 될 거예요.</span>
          </div>
        </div>
        <div className="flex flex-col gap-6">
          <h2 className="m-0 text-[28px] font-extrabold text-ink">이렇게 진행돼요</h2>
          <div className="grid grid-cols-5 border-t-2 border-ink">
            {STEPS.map((label, i) => (
              <div key={label} className="pr-5 py-[22px] flex flex-col gap-1.5 border-b border-line">
                <span className="text-[15px] font-extrabold text-accent">STEP {i + 1}</span>
                <span className="text-[20px] font-extrabold text-ink">{label}</span>
                <span className="text-[16px] text-sub leading-[1.55]">{STEP_DESC[i]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// 재취업 이야기: 내용은 팀이 정한다(TEAM W3). 오기 전에는 시안의 자리표시 그대로.
const STORY = [
  { num: '○○만 명', label: '[자리표시] 다시 일을 찾는 40~50대', src: '[출처 기관, 연도]', h: '[자리표시] 일을 쉬었던 시간은 생각보다 흔해요', p: '[자리표시 문단] 육아, 가족 돌봄, 회사 사정처럼 여러 이유로 일을 멈췄던 사람들이 다시 일자리를 찾고 있어요. 확정된 통계와 짧은 설명이 이 자리에 들어가요.' },
  { num: '○○%', label: '[자리표시] 공백이 있어도 재취업에 성공한 비율', src: '[출처 기관, 연도]', h: '[자리표시] 문제는 경력이 아니라 ‘설명하는 방법’이에요', p: '[자리표시 문단] 오래전 경력과 아르바이트, 자격증도 지금의 일과 이어질 수 있어요. 다만 그것을 공고의 말로 바꿔 설명하기가 어려울 뿐이에요.' },
  { num: '○.○년', label: '[자리표시] 평균 경력 공백 기간', src: '[출처 기관, 연도]', h: '[자리표시] 공백 기간도 하나의 경험이에요', p: '[자리표시 문단] 살림, 돌봄, 지역 활동에서 쌓은 꼼꼼함과 책임감은 많은 공고가 찾는 힘이에요. 원하실 때만 경험으로 넣을 수 있어요.' },
  { num: '○,○○○개', label: '[자리표시] 들을 수 있는 국비 교육과정', src: '[출처 기관, 연도]', h: '[자리표시] 부족한 부분은 나라가 함께 채워요', p: '[자리표시 문단] 국민내일배움카드로 훈련비를 지원받을 수 있어요. 내 역량에서 부족한 것만 골라 배우면 돼요.' },
]

export function Story() {
  const stat = b => (
    <div className="border border-line rounded-[20px] px-10 py-11 flex flex-col gap-2.5 shadow-[0_8px_24px_rgba(14,35,80,.06)]">
      <span className="text-[76px] font-extrabold text-brand leading-none tracking-[-0.03em]">{b.num}</span>
      <span className="text-[20px] font-bold text-ink">{b.label}</span>
      <span className="text-[15px] text-sub">출처: {b.src}</span>
    </div>
  )
  const text = b => <div><h2 className="m-0 mb-3.5 text-[30px] font-extrabold text-ink leading-[1.4] text-balance">{b.h}</h2><p className="m-0 text-[19px] leading-[1.8] text-sub">{b.p}</p></div>
  return (
    <div className="flex-1 min-h-0 overflow-y-auto bg-white">
      <div className="bg-[linear-gradient(180deg,#EAF5FD_0%,#FFFFFF_100%)] px-12 pt-20 pb-12">
        <div className="max-w-[1080px] mx-auto flex flex-col gap-[18px]">
          <h1 className="m-0 text-[48px] font-extrabold text-ink leading-[1.3] tracking-[-0.02em] max-w-[820px] text-balance">[자리표시] 다시 일을 시작하는 사람이 늘고 있어요</h1>
          <p className="m-0 text-[20px] text-sub max-w-[720px]">[자리표시] 왜 중장년 재취업이 필요한지, 숫자와 짧은 이야기로 전해 드려요. 문구와 숫자는 확정되면 바꿔 넣을 예정이에요.</p>
        </div>
      </div>
      <div className="max-w-[1080px] mx-auto px-12 pt-6 pb-20 flex flex-col gap-[72px]">
        {STORY.map((b, i) => (
          <div key={b.num} className="grid grid-cols-2 gap-14 items-center">{i % 2 ? <>{text(b)}{stat(b)}</> : <>{stat(b)}{text(b)}</>}</div>
        ))}
        <div className="border-t-2 border-ink pt-14 text-center flex flex-col items-center gap-4">
          <h2 className="m-0 text-[34px] font-extrabold text-ink leading-[1.4]">지나온 시간도 모두 경험이에요</h2>
          <p className="m-0 text-[19px] text-sub">해 오신 일을 들려주시면, 지금 할 수 있는 일을 함께 찾아 드릴게요.</p>
          <Btn size="xl" className="mt-2 font-extrabold" onClick={start}>내 경험으로 시작하기 →</Btn>
        </div>
      </div>
    </div>
  )
}

// ⑥ 공고 분석: 붙여 넣은 공고를 구절로 나눠 종류와 역량을 보여 준다(지금은 규칙만, AI 보완은 BACKLOG B21)
const SAMPLE = '[한빛로지스 송파물류센터] 재고관리 사무원 모집\n- 물류센터 입고 상품 검수 및 재고 수량 확인\n- 월말 재고 실사 및 결과 보고\n- 엑셀로 재고 현황표 작성 가능하신 분\n- 재고 관리 경력 1년 이상\n- ERP 사용 경험자 우대\n- 지게차 운전 기능사 소지자 우대\n- 근무시간 09:00~15:00, 주 5일\n- 시급 11,500원, 계약직 1년(연장 가능)\n- 책임감 있고 꼼꼼한 분'
const TY = { 필수: 'text-brand', 우대: 'text-teal', 업무: 'text-ok', 조건: 'text-sub', 정책우대: 'text-teal' }
const TY_LABEL = { 조건: '근무 조건', 정책우대: '정책 우대' }

export function Analyze() {
  const { meta } = useApp()
  const [text, setText] = useState('')
  const [st, setSt] = useState({ phase: 'idle' })   // idle | loading | done | error
  const [pick, setPick] = useState(null)
  const run = async () => {
    if (!text.trim()) return setSt({ phase: 'error', msg: '공고 글이 비어 있어요.', empty: true })
    setSt({ phase: 'loading' }); setPick(null)
    try { setSt({ phase: 'done', r: await api('analyze-posting', { text }) }) } catch (e) { setSt({ phase: 'error', msg: e.message }) }
  }
  const r = st.r
  const names = {}
  if (r) for (const x of [...r.requirements, ...r.display_only, ...r.filters]) names[x.kw_idx] = x.keyword
  const att = new Set(r ? r.display_only.map(x => x.kw_idx) : [])
  const skills = r ? [...r.requirements.map(x => ({ ...x, ty: x.type })), ...r.display_only.map(x => ({ ...x, ty: '태도' }))] : []
  const picked = skills[pick]
  return (
    <div className="flex-1 min-h-0 overflow-y-auto bg-white">
      <div className="max-w-[1360px] mx-auto px-12 pt-10 pb-16 flex flex-col gap-7">
        <H1 title="채용공고를 붙여 넣으면 한 구절씩 나눠 읽어 드려요" sub="구절마다 필수인지, 우대인지, 하게 될 업무인지, 근무 조건인지 알려 드리고 거기서 찾은 역량을 보여 드려요." />
        <div className="flex flex-col gap-2.5">
          <label className="text-[16px] font-bold text-sub" htmlFor="ad">공고 글</label>
          <textarea id="ad" value={text} onChange={e => setText(e.target.value)} rows={6} maxLength={10000} placeholder="채용 누리집의 공고 내용을 복사해서 붙여 넣어 주세요."
            className="field px-4 py-3.5 rounded-xl text-[17px] leading-[1.7] resize-y" />
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-[15px] text-muted flex-1">{text.length}자</span>
            <Btn kind="plain" onClick={() => { setText(''); setSt({ phase: 'idle' }) }} className="h-12 text-[17px] font-normal">지우기</Btn>
            <Btn kind="outline" onClick={() => setText(SAMPLE)} className="h-12 text-[17px]">예시 공고 넣기</Btn>
            <Btn size="lg" onClick={run} disabled={st.phase === 'loading'}>공고 나눠 읽기</Btn>
          </div>
        </div>
        {st.phase === 'error' && (
          <div role="alert" className="px-[22px] py-[18px] rounded-xl border border-err flex items-center gap-4 flex-wrap">
            <span className="flex-1 text-[18px] text-body"><b className="text-err">{st.msg}</b>{st.empty && ' 공고 내용을 붙여 넣거나 ‘예시 공고 넣기’를 눌러 주세요.'}</span>
            {st.empty ? <Btn kind="outline" onClick={() => { setText(SAMPLE); setSt({ phase: 'idle' }) }}>예시 공고 넣기</Btn> : <Btn onClick={run}>다시 시도하기</Btn>}
          </div>
        )}
        {st.phase === 'idle' && <div className="p-12 rounded-2xl border-[1.5px] border-dashed border-field text-center text-[18px] text-sub">공고 글을 넣고 ‘공고 나눠 읽기’를 누르면 결과가 여기에 나와요.</div>}
        {st.phase === 'loading' && (
          <div role="status" className="py-8 flex items-center gap-[18px]"><Spinner size={40} />
            <div><div className="text-[21px] font-extrabold text-ink">공고를 구절로 나누는 중이에요</div><div className="text-[17px] text-sub">역량 사전 182개와 맞춰 보고 있어요.</div></div></div>
        )}
        {st.phase === 'done' && <>
          <div className="flex items-center gap-3.5 flex-wrap py-3.5 border-y border-line text-[15px]">
            <span className="font-bold text-sub">구절 종류</span>
            {['필수', '우대', '업무', '조건'].map(t => <span key={t} className={`font-bold ${TY[t]}`}>{TY_LABEL[t] || t}</span>)}
            <span className="w-px h-[22px] bg-line mx-1.5" />
            <span className="text-sub">{meta ? `실제 공고 ${meta.postings.toLocaleString('ko-KR')}건도 같은 규칙으로 미리 나눠 두었어요.` : ''}</span>
          </div>
          <div className="grid grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)] gap-10 items-start">
            <div className="flex flex-col">
              <h2 className="m-0 mb-3 text-[22px] font-extrabold text-ink">구절 {r.clauses.length}개로 나눴어요</h2>
              <div className="border-t-2 border-ink">
                {r.clauses.map((c, i) => {
                  const on = picked && picked.clause_id === c.clause_id
                  return (
                    <div key={c.clause_id} className={`grid grid-cols-[28px_92px_minmax(0,1fr)] gap-3 items-start px-3 py-3.5 border-b border-line2 ${on ? 'rounded-lg shadow-[inset_0_0_0_2px_#12307A]' : ''}`}>
                      <span className="text-[15px] font-bold text-muted pt-0.5">{i + 1}</span>
                      <span className={`justify-self-start text-[14px] font-bold whitespace-nowrap ${TY[c.type] || 'text-sub'}`}>{TY_LABEL[c.type] || c.type}</span>
                      <div className="flex flex-col gap-2 min-w-0">
                        <span className="text-[18px] text-ink leading-[1.55]">{c.text}{c.kw.some(k => att.has(k)) && <span className="ml-2 text-[14px] text-sub">(태도 요구)</span>}</span>
                        <div className="flex flex-wrap gap-1.5">
                          {c.kw.filter(k => names[k]).map(k => {
                            const idx = skills.findIndex(x => x.kw_idx === k && (x.clause_id === c.clause_id || x.quote === c.text))
                            return <button key={k} onClick={() => setPick(idx >= 0 ? idx : null)} className="h-[34px] px-3 rounded-md border border-brand bg-white text-brand text-[15px] font-bold">{names[k]}</button>
                          })}
                          {!c.kw.length && <span className="text-[15px] text-muted">{c.type === '조건' ? '근무 조건이라 역량은 없어요' : '사전에 있는 역량을 찾지 못했어요'}</span>}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
            <div className="border border-line rounded-[20px] p-6 flex flex-col sticky top-0">
              <h2 className="m-0 text-[22px] font-extrabold text-ink">찾은 역량 {skills.length}개</h2>
              <div className="text-[16px] text-sub mt-1 mb-2.5">규칙으로 찾았어요 · 누르면 원문 구절을 표시해요</div>
              {skills.map((x, i) => (
                <button key={i} onClick={() => setPick(i)} className={`text-left px-2.5 py-3 border-0 border-b border-line2 bg-white flex flex-col gap-1.5 hover:bg-hover ${pick === i ? 'rounded-lg shadow-[inset_0_0_0_2px_#12307A]' : ''}`}>
                  <div className="flex items-center gap-2 flex-wrap w-full">
                    <span className="flex-1 min-w-0 text-[17px] font-extrabold text-ink">{x.keyword}</span>
                    <span className={`text-[14px] font-bold ${TY[x.ty] || 'text-sub'}`}>{x.ty}</span>
                  </div>
                  {pick === i && <span className="text-[15px] text-body leading-[1.55]">원문 구절 · “{x.quote}”</span>}
                </button>
              ))}
              {!skills.length && <span className="text-[17px] text-sub py-4">역량 사전과 맞는 표현을 찾지 못했어요.</span>}
            </div>
          </div>
        </>}
      </div>
    </div>
  )
}
