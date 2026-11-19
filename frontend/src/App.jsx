import { useEffect, useRef, useState } from 'react'
import { api, setTape, tapeInfo, tapeJson } from './api'
import {
  PERSONAS, STEPS, STEP_LABEL, TYPE_LABEL, cardsIn, courses, focusChat, get, goStep, loadPersona, postings, recommend, reset,
  selectedPost, send, set, start, toCards, useApp,
} from './store'
import { AiDot, Btn, EmptyArt, Logo, Spinner } from './ui'
import { Step1, Step2, Step3, Step4, Step5 } from './steps'
import { Analyze, Landing, Story } from './pages'

export default function App() {
  const s = useApp()
  useEffect(() => { api('meta').then(meta => set({ meta })).catch(() => {}) }, [])
  return (
    <div className="h-screen min-w-[1024px] flex flex-col font-sans text-body text-[18px] leading-[1.6] relative overflow-hidden bg-white">
      {s.screen === 'landing' ? <Landing /> : <>
        <Header s={s} />
        {s.screen === 'work' && <Work s={s} />}
        {s.screen === 'story' && <Story />}
        {s.screen === 'analyze' && <Analyze />}
      </>}
      {s.drawer && <MyDrawer s={s} />}
      <Demo s={s} />
    </div>
  )
}

function Header({ s }) {
  const work = s.screen === 'work'
  const saved = s.cards.filter(c => c.saved).length
  const tab = on => `px-3 text-[16px] font-bold text-ink ${on ? 'shadow-[inset_0_-3px_0_#12307A]' : ''}`
  return (
    <header className="h-[76px] shrink-0 flex items-stretch gap-4 px-5 border-b border-line bg-white relative z-[5]">
      <button onClick={() => set({ screen: 'landing' })} title="첫 화면으로" className="flex items-center shrink-0 bg-transparent border-0 p-0"><Logo small /></button>
      <nav aria-label="진행 단계" className="flex-1 min-w-0 flex justify-center items-stretch gap-0.5">
        {STEPS.map((label, i) => {
          const k = i + 1, cur = work && k === s.step, done = !cur && k <= s.maxStep
          return (
            <div key={k} className="flex items-stretch gap-0.5">
              {cur ? (
                <div aria-current="step" className="flex items-center gap-2 px-2.5 shadow-[inset_0_-3px_0_#12307A]">
                  <span className="size-7 rounded-full bg-brand text-white text-[14px] font-extrabold flex items-center justify-center">{k}</span>
                  <span className="text-[16px] font-extrabold text-ink whitespace-nowrap">{label}</span>
                </div>
              ) : done ? (
                <button onClick={() => goStep(k)} title={`${k}단계로 돌아가기`} className="flex items-center gap-2 px-2.5 border-0 bg-transparent hover:shadow-[inset_0_-3px_0_#C3CEDC]">
                  <span className="size-7 rounded-full border-[1.5px] border-brand text-brand text-[14px] font-extrabold flex items-center justify-center">{k < s.maxStep || !work ? '✓' : k}</span>
                  <span className="hidden xl:inline text-[16px] font-bold text-brand whitespace-nowrap">{label}</span>
                </button>
              ) : (
                <div className="flex items-center gap-2 px-2.5" title={label}>
                  <span className="size-7 rounded-full border-[1.5px] border-field text-muted text-[14px] flex items-center justify-center">{k}</span>
                  <span className="hidden xl:inline text-[16px] text-muted whitespace-nowrap">{label}</span>
                </div>
              )}
              {k < 5 && <span className="self-center text-[14px] text-[#A6B1C2]">›</span>}
            </div>
          )
        })}
      </nav>
      <div className="flex items-stretch gap-0.5 shrink-0">
        <button onClick={() => set({ screen: 'story' })} className={`border-0 bg-transparent ${tab(s.screen === 'story')}`}>재취업 이야기</button>
        <button onClick={() => set({ screen: 'analyze' })} className={`border-0 bg-transparent ${tab(s.screen === 'analyze')}`}>공고 분석</button>
        <div className="flex items-center ml-2">
          <Btn kind="outline" onClick={() => set({ drawer: true })}>내 경험 <b className="font-extrabold">{saved}</b></Btn>
        </div>
      </div>
    </header>
  )
}

const EMPTY = {
  2: ['아직 경험 카드가 없어요', '오른쪽 대화창에 해 오신 일을 한두 문장 적어 주시면 AI 도우미가 경험 카드 초안을 만들어 드려요.', '대화로 시작하기', focusChat],
  3: ['추천할 직무를 찾지 못했어요', '경험 카드에서 직무와 이어지는 역량을 찾지 못했어요. 하신 일을 조금 더 자세히 들려주시면 다시 찾아볼게요.', '② 경험 카드로 가기', () => goStep(2)],
  4: ['아직 공고를 불러오지 않았어요', '직무 추천에서 직무를 고르고 ‘이 직무 공고 보기’를 눌러 주세요.', '③ 직무 추천으로 가기', () => goStep(3)],
  5: ['아직 교육과정을 찾지 않았어요', '채용공고에서 공고를 고르고 ‘부족한 역량 채우기’를 눌러 주세요.', '④ 채용공고로 가기', () => goStep(4)],
  '5none': ['교육으로 채울 역량이 없어요', '고른 공고가 요구하는 핵심 역량은 이미 갖고 계세요.', '④ 채용공고로 돌아가기', () => goStep(4)],
}

function emptyKey(s) {
  if (s.step === 2 && !s.cards.length) return 2
  if (s.step === 3 && !s.jobs?.length) return 3
  if (s.step === 4 && !s.posts) return 4
  if (s.step === 5) return !s.gaps ? 5 : !s.gaps.length ? '5none' : null
  return null
}

function Work({ s }) {
  const mainRef = useRef(null)
  useEffect(() => { if (mainRef.current) mainRef.current.scrollTop = 0 }, [s.step])
  const busy = s.busy?.step === s.step && s.busy, err = !busy && s.err?.step === s.step && s.err
  const ek = !busy && !err && emptyKey(s)
  const STEP = [null, Step1, Step2, Step3, Step4, Step5][s.step]
  return (
    <div className="flex-1 min-h-0 flex bg-white">
      <main className="flex-1 min-w-0 flex flex-col">
        <div ref={mainRef} className="flex-1 min-h-0 overflow-y-auto">
          <div className="max-w-[1080px] mx-auto px-8 xl:px-12 pt-10 pb-14">
            {busy ? <Loading b={busy} /> : err ? <ErrorBox e={err} /> : ek ? <Empty e={EMPTY[ek]} /> : <STEP s={s} />}
          </div>
        </div>
        {!busy && !err && !ek && <ActionBar s={s} />}
      </main>
      <Chat s={s} />
    </div>
  )
}

function Loading({ b }) {
  return (
    <div className="min-h-[560px] flex items-center justify-center">
      <div role="status" className="w-full max-w-[580px] border border-line rounded-[20px] p-10 flex flex-col gap-5">
        <Spinner />
        <div>
          <h2 className="m-0 mb-1.5 text-[26px] font-extrabold text-ink leading-[1.4]">{b.title}</h2>
          <p className="m-0 text-[18px] text-sub">{b.sub}</p>
        </div>
        <div className="pt-4 border-t border-line2 text-[16px] text-sub">보통 몇 초 안에 끝나요. AI가 글을 정리할 때는 10초쯤 걸릴 수 있어요.</div>
      </div>
    </div>
  )
}

function ErrorBox({ e }) {
  return (
    <div className="min-h-[560px] flex items-center justify-center">
      <div role="alert" className="w-full max-w-[600px] border-[1.5px] border-[#E7A39B] rounded-[20px] p-10 flex flex-col gap-4">
        <div className="size-[52px] rounded-full border-2 border-err text-err text-[28px] font-extrabold flex items-center justify-center">!</div>
        <h2 className="m-0 text-[26px] font-extrabold text-ink">{e.title}</h2>
        <p className="m-0 text-[18px] text-sub">{e.sub} 입력하신 경험 카드와 대화는 그대로 남아 있어요.</p>
        <div className="flex gap-3 mt-2 flex-wrap">
          <Btn size="lg" onClick={e.retry}>다시 시도하기</Btn>
          <Btn size="lg" kind="outline" onClick={focusChat}>대화창에 물어보기</Btn>
        </div>
      </div>
    </div>
  )
}

function Empty({ e }) {
  return (
    <div className="min-h-[560px] flex flex-col items-center justify-center text-center gap-4">
      <EmptyArt />
      <h2 className="mt-2 mb-0 text-[28px] font-extrabold text-ink">{e[0]}</h2>
      <p className="m-0 max-w-[520px] text-[18px] text-sub text-pretty">{e[1]}</p>
      <Btn size="lg" className="mt-2" onClick={e[3]}>{e[2]}</Btn>
    </div>
  )
}

function ActionBar({ s }) {
  const job = s.jobs?.[s.jobSel], post = selectedPost(s)
  const saved = s.cards.filter(c => c.saved).length
  const miss = post && [...post.required, ...post.preferred, ...post.tasks].filter(x => !x.has).length + post.needs_license.length
  const a = {
    1: [`모은 경험 ${s.cards.length}개 · 나눈 대화 ${s.msgs.filter(m => m.r === 'u').length}번`, '경험 카드 만들기', toCards],
    2: [`저장한 카드 ${saved}장 / 초안 ${s.cards.length}장${saved ? '' : ' · 저장한 카드가 없으면 초안을 모두 써요'}`, '직무 추천 받기', recommend],
    3: [job && `고른 직무: ${job.name} · ${job.score.toFixed(1)}점`, '이 직무 공고 보기', postings],
    4: [post ? `고른 공고: ${post.company} · 부족한 역량 ${miss}개` : '공고 없이 직무 기준으로 찾아요', '부족한 역량 채우기', courses],
    5: ['마지막 단계예요. 정리한 경험은 ‘내 경험’에 남아 있어요.', '내 경험 열어 보기', () => set({ drawer: true })],
  }[s.step]
  return (
    <div className="shrink-0 border-t border-line bg-white px-8 xl:px-12 py-3.5 flex items-center gap-4">
      {s.step > 1 && <Btn kind="plain" size="lg" onClick={() => goStep(s.step - 1)}>← 이전 단계</Btn>}
      <span className="flex-1 min-w-0 text-[17px] text-sub">{a[0]}</span>
      <Btn size="xl" onClick={a[2]} disabled={s.typing && s.step <= 2}>{a[1]} →</Btn>
    </div>
  )
}

// ---------------- 대화창 ----------------
function Chat({ s }) {
  const [drag, setDrag] = useState(null)   // 끄는 중의 비율(끝나면 저장)
  const listRef = useRef(null), boxRef = useRef(null)
  const [input, setInput] = useState('')
  useEffect(() => { const el = listRef.current; if (el) el.scrollTop = el.scrollHeight }, [s.msgs.length, s.typing, s.chatOpen])
  useEffect(() => {
    if (drag === null) return
    const move = e => {
      const r = boxRef.current.parentElement.getBoundingClientRect()
      setDrag(Math.min(0.5, Math.max(0.24, (r.right - e.clientX) / r.width)))
    }
    const up = () => { set({ chatRatio: drag }); setDrag(null); document.body.style.cursor = '' }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
    return () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
  }, [drag])

  if (!s.chatOpen) return (
    <button onClick={() => set({ chatOpen: true })} className="shrink-0 w-[68px] border-0 border-l border-line bg-white flex flex-col items-center py-6 gap-3.5">
      <AiDot size={14} />
      <span className="[writing-mode:vertical-rl] text-[17px] font-bold text-brand tracking-[.05em]">‹ AI 대화창 열기</span>
    </button>
  )
  const ratio = drag ?? s.chatRatio
  const go = t => { send(t); setInput('') }
  const last = s.msgs.at(-1)
  const agentMode = s.step >= 3
  return <>
    <div ref={boxRef} onMouseDown={e => { e.preventDefault(); document.body.style.cursor = 'col-resize'; setDrag(s.chatRatio) }}
      onDoubleClick={() => set({ chatRatio: 1 / 3 })} title="끌어서 너비를 바꿀 수 있어요 · 두 번 누르면 처음 크기로" role="separator" aria-orientation="vertical"
      className={`shrink-0 w-4 cursor-col-resize relative flex items-center justify-center hover:bg-[#F3F7FB] select-none ${drag !== null ? 'bg-[#F3F7FB]' : 'bg-white'}`}>
      <div className="absolute inset-y-0 left-[7.5px] w-px bg-line" />
      <div className="relative w-3 h-[60px] rounded-md bg-white border border-dash flex flex-col items-center justify-center gap-[5px]">
        {[0, 1, 2].map(i => <span key={i} className="size-1 rounded-full bg-sub" />)}
      </div>
      {drag !== null && <div className="absolute top-1/2 left-[22px] -translate-y-1/2 whitespace-nowrap h-8 px-2.5 rounded-md bg-ink text-white text-[15px] font-bold flex items-center z-[3]">대화창 {Math.round(ratio * 100)}%</div>}
    </div>
    <aside aria-label="AI 대화창" className={`min-w-0 flex flex-col bg-white ${drag !== null ? 'select-none' : ''}`} style={{ flex: `0 0 ${(ratio * 100).toFixed(2)}%` }}>
      <div className="shrink-0 h-[68px] flex items-center gap-3 pl-6 pr-5 border-b border-line2">
        <AiDot size={14} />
        <div className="flex-1 min-w-0 flex flex-col leading-[1.3]">
          <span className="text-[18px] font-extrabold text-ink">AI 커리어 도우미</span>
          <span className="text-[14px] text-sub truncate">{agentMode ? '직무·공고·교육과정을 물어보세요' : '해 오신 일을 하나씩 여쭤볼게요'}</span>
        </div>
        <Btn kind="plain" size="sm" onClick={() => set({ chatOpen: false })}>대화창 접기 ›</Btn>
      </div>
      <div ref={listRef} className="flex-1 min-h-0 overflow-y-auto px-6 pt-6 pb-3 flex flex-col gap-6">
        {s.msgs.map(m => m.r === 'u' ? (
          <div key={m.id} className="msg-in self-end max-w-[86%] px-[18px] py-3.5 rounded-2xl bg-soft text-[18px] leading-[1.6] text-ink whitespace-pre-line">{m.t}</div>
        ) : (
          <div key={m.id} className="msg-in flex flex-col gap-2.5">
            <div className="flex items-center gap-2.5">
              <AiDot size={12} /><span className="text-[16px] font-extrabold text-ink">AI 답변</span>
              {m.step > 1 && <span className="text-[14px] text-sub">· {STEP_LABEL[m.step]}</span>}
            </div>
            <div className={`text-[18px] leading-[1.7] whitespace-pre-line text-pretty ${m.error ? 'text-err' : 'text-ink'}`}>{m.t}</div>
            {m === last && m.chips && !s.typing && (
              <div className="flex flex-wrap gap-2">
                {m.chips.map(c => (
                  <button key={c} onClick={() => go(c)} className="min-h-[44px] px-[18px] py-2 rounded-full border border-field bg-white text-brand text-[16px] font-bold shadow-[0_2px_6px_rgba(14,35,80,.06)] text-left hover:border-brand">{c}</button>
                ))}
              </div>
            )}
          </div>
        ))}
        {(s.typing || s.busy) && (
          <div role="status" className="flex items-center gap-3">
            <span className="ai-dot pulse" style={{ width: 14, height: 14 }} />
            <span className="text-[17px] text-ink font-bold">{s.typing ? (agentMode ? '자료를 찾아 답을 정리하는 중이에요… 보통 5~10초 걸려요' : '답을 정리하는 중이에요…') : s.busy.title}</span>
          </div>
        )}
      </div>
      <div className="shrink-0 px-5 pt-3 pb-3.5">
        <div className="border border-field rounded-2xl bg-white px-4 pt-3.5 pb-3 flex flex-col gap-2">
          <textarea id="chat-input" value={input} onChange={e => setInput(e.target.value)} maxLength={300} rows={2}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); if (!s.typing) go(input) } }}
            placeholder={agentMode ? '추천 직무나 공고, 교육과정에 대해 물어보세요.' : '해 오신 일을 편하게 적어 주세요.'}
            className="border-0 outline-none resize-none text-[18px] leading-[1.6] text-ink bg-transparent w-full" />
          <div className="flex items-center justify-between gap-2.5">
            <span className="text-[15px] text-muted">{input.length}/300</span>
            <Btn onClick={() => go(input)} disabled={s.typing || !input.trim()}>보내기 ↑</Btn>
          </div>
        </div>
        <div className="text-center text-[14px] text-sub mt-2">AI는 실수할 수 있어요. 중요한 내용은 한 번 더 확인해 주세요.</div>
      </div>
    </aside>
  </>
}

// ---------------- 내 경험 서랍 ----------------
function MyDrawer({ s }) {
  const saved = s.cards.filter(c => c.saved)
  const close = () => set({ drawer: false })
  return <>
    <div onClick={close} className="absolute inset-0 bg-[rgba(14,35,80,.28)] z-40" />
    <div role="dialog" aria-label="내 경험" className="slide-in absolute inset-y-0 right-0 w-[480px] max-w-[92vw] bg-white z-[41] shadow-[-16px_0_48px_rgba(14,35,80,.18)] flex flex-col">
      <div className="shrink-0 px-7 py-6 border-b border-line2 flex items-center gap-3">
        <div className="flex-1"><h2 className="m-0 text-[26px] font-extrabold text-ink">내 경험</h2><div className="text-[16px] text-sub">저장한 경험 카드 {saved.length}장</div></div>
        <Btn kind="plain" onClick={close}>닫기 ✕</Btn>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto px-7 pt-2 pb-5 flex flex-col">
        {saved.length ? saved.map(c => (
          <div key={c.id} className="py-5 border-b border-line flex flex-col gap-2">
            <div className="flex items-center gap-2 text-[15px]"><span className="font-bold text-accent">{TYPE_LABEL[c.card.type]}</span>
              {c.card.slots.period?.value && <><span className="text-[#A6B1C2]">|</span><span className="text-sub">{c.card.slots.period.value}</span></>}</div>
            <div className="text-[20px] font-extrabold text-ink">{c.card.activity}</div>
            <div className="text-[16px] text-sub">역량 · {c.competencies.filter(k => !c.removed.includes(k.kw_idx)).map(k => k.keyword).join(' · ') || '아직 없음'}</div>
            <Btn kind="outline" className="self-start mt-1" onClick={() => set({ drawer: false, screen: 'work', step: 2, cardSel: s.cards.indexOf(c), maxStep: Math.max(s.maxStep, 2) })}>카드 열어 고치기</Btn>
          </div>
        )) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center gap-3.5 px-3 py-10">
            <EmptyArt size={80} />
            <div className="text-[22px] font-extrabold text-ink">아직 저장한 경험 카드가 없어요</div>
            <p className="m-0 text-[17px] text-sub">경험 카드 단계에서 초안을 확인하고 ‘이 카드 저장하기’를 누르면 여기에 모여요.</p>
            {s.cards.length > 0 && <Btn size="lg" onClick={() => { close(); toCards() }}>경험 카드 확인하러 가기</Btn>}
          </div>
        )}
      </div>
      <div className="shrink-0 px-7 py-4 border-t border-line2">
        <Btn kind="outline" size="lg" className="w-full" onClick={() => { set({ drawer: false, screen: 'work', step: 1 }); if (!s.msgs.length) start(); focusChat() }}>+ 새 경험 더 모으기</Btn>
      </div>
    </div>
  </>
}

// ---------------- 시연 도구(왼쪽 아래, DESIGN 6절) ----------------
function Demo({ s }) {
  const b = 'h-8 rounded-md border bg-[#1F232B] text-[#E6E8EE] font-[inherit] text-[12px] disabled:opacity-40'
  const t = tapeInfo()
  const tape = (mode, calls) => { setTape(mode, calls); set({}) }   // set({}): 서랍을 다시 그림
  const download = () => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([tapeJson()], { type: 'application/json' }))
    a.download = 'careerlens-녹화본.json'
    a.click()
  }
  const upload = async e => {
    try {
      const calls = JSON.parse(await e.target.files[0].text())
      if (!Array.isArray(calls) || !calls.every(c => c.path && 'res' in c)) throw 0
      tape('off', calls)
    } catch { alert('녹화본 파일이 아니에요.') }
    e.target.value = ''
  }
  return <>
    <button onClick={() => set({ demo: !s.demo })} title="시연 도구"
      className={`absolute left-2.5 bottom-2.5 z-[60] h-7 px-2.5 rounded-md border text-[11px] font-mono tracking-[.04em] ${t.mode === 'off'
        ? 'border-line bg-white/85 text-faint opacity-50 hover:opacity-100'
        : t.mode === 'play' ? 'border-[#C99A1E] bg-[#FFF4D1] text-[#6B4E00] font-bold' : 'border-[#D9534F] bg-[#FDECEA] text-[#9B2C2C] font-bold'}`}>
      {t.mode === 'play' ? 'DEMO · 재생 중(저장한 응답)' : t.mode === 'rec' ? 'DEMO · ● 녹화 중' : 'DEMO'}</button>
    {s.demo && (
      <div className="msg-in absolute left-2.5 bottom-[46px] z-[61] w-[340px] bg-[#16181D] text-[#E6E8EE] rounded-xl overflow-hidden shadow-[0_20px_48px_rgba(0,0,0,.4)] font-mono text-[13px] leading-[1.4]">
        <div className="h-2 bg-[repeating-linear-gradient(135deg,#F5C84C_0_10px,#16181D_10px_20px)]" />
        <div className="flex items-center justify-between px-3.5 pt-3 pb-1.5">
          <span className="font-bold tracking-[.06em] text-[#F5C84C]">시연 도구 · 발표용</span>
          <button onClick={() => set({ demo: false })} className="bg-transparent border border-[#3A3F4B] text-[#E6E8EE] rounded-md h-[26px] px-2 text-[12px]">닫기</button>
        </div>
        <div className="px-3.5 pt-1.5 pb-3.5 flex flex-col gap-3.5">
          <button onClick={() => reset({ demo: true })} className="h-9 rounded-lg border border-[#F07A6E] bg-transparent text-[#FFB4AB] text-[13px]">↺ 처음부터 다시 시작</button>
          <div className="flex flex-col gap-1.5"><span className="text-[#8B93A5]">예시 인물 불러오기 (AI 호출 2~4번)</span>
            {PERSONAS.map(p => (
              <button key={p.name} onClick={() => loadPersona(p)} disabled={!!s.busy}
                className="text-left px-2.5 py-2 rounded-lg border border-[#3A3F4B] bg-[#1F232B] text-[#E6E8EE] text-[13px] disabled:opacity-40"><b>{p.name}</b> · {p.desc}</button>
            ))}
          </div>
          <div className="flex flex-col gap-1.5"><span className="text-[#8B93A5]">단계로 바로 가기 (거친 단계까지)</span>
            <div className="grid grid-cols-6 gap-1">
              <button onClick={() => set({ screen: 'landing' })} className={`${b} border-[#3A3F4B]`}>첫</button>
              {[1, 2, 3, 4, 5].map(k => (
                <button key={k} onClick={() => k === 1 ? start() : goStep(k)} disabled={k > s.maxStep}
                  className={`${b} ${s.screen === 'work' && s.step === k ? 'border-[#F5C84C]' : 'border-[#3A3F4B]'}`}>{k}</button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1">
            <button onClick={() => set({ screen: 'story' })} className={`${b} border-[#3A3F4B]`}>재취업 이야기</button>
            <button onClick={() => set({ screen: 'analyze' })} className={`${b} border-[#3A3F4B]`}>공고 분석</button>
            <button onClick={() => set({ chatRatio: 1 / 3, chatOpen: true })} className={`${b} border-[#3A3F4B]`}>대화창 너비 처음대로</button>
            <button onClick={() => set({ chatOpen: !get().chatOpen })} className={`${b} border-[#3A3F4B]`}>대화창 접기/펴기</button>
          </div>
          <div className="flex flex-col gap-1.5"><span className="text-[#8B93A5]">녹화·재생 (서버·Bedrock 장애 대비) · 녹화본 응답 {t.n}개</span>
            <div className="grid grid-cols-3 gap-1">
              <button onClick={() => tape(t.mode === 'rec' ? 'off' : 'rec')} disabled={t.mode === 'play'}
                className={`${b} ${t.mode === 'rec' ? 'border-[#F07A6E]' : 'border-[#3A3F4B]'}`}>{t.mode === 'rec' ? '■ 녹화 끝' : '● 새로 녹화'}</button>
              <button onClick={() => tape(t.mode === 'play' ? 'off' : 'play')} disabled={!t.n || t.mode === 'rec'}
                className={`${b} ${t.mode === 'play' ? 'border-[#F5C84C]' : 'border-[#3A3F4B]'}`}>{t.mode === 'play' ? '■ 재생 끝' : '▶ 재생'}</button>
              <button onClick={download} disabled={!t.n} className={`${b} border-[#3A3F4B]`}>내려받기</button>
            </div>
            <label className={`${b} border-[#3A3F4B] flex items-center justify-center cursor-pointer`}>
              녹화본 파일 불러오기<input type="file" accept=".json,application/json" onChange={upload} className="hidden" />
            </label>
            <span className="text-[#8B93A5] text-[12px]">새로 녹화하면 이전 녹화본은 지워져요. 재생 중에 녹화본에 없는 요청은 실제 서버로 가요.</span>
          </div>
          <div className="text-[#8B93A5] text-[12px]">카드 {s.cards.length}장 · 추천에 쓰는 카드 {s.cards.length ? cardsIn().length : 0}장</div>
        </div>
      </div>
    )}
  </>
}
