// 화면 상태 한 곳. 서버는 사용자 상태를 들지 않으므로 경험 카드·대화·단계 결과를 모두 여기 들고 있다가
// 요청마다 보낸다. 새로 고침해도 남도록 브라우저 저장소에 둔다(화면 품질 기준 5, BACKLOG B20).
import { useSyncExternalStore } from 'react'
import { api } from './api'

const KEY = 'careerlens-v1'
const TRANSIENT = ['busy', 'err', 'typing', 'drawer', 'demo', 'meta', 'postsLoading']

export const STEPS = ['경험 수집', '경험 카드', '직무 추천', '채용공고', '교육과정 추천']
export const STEP_LABEL = ['', '① 경험 수집', '② 경험 카드', '③ 직무 추천', '④ 채용공고', '⑤ 교육과정 추천']
export const TYPE_LABEL = {
  job: '직장 경력', internship: '인턴', part_time: '아르바이트·단기 일', self_employed: '자영업·가게 운영', project: '프로젝트',
  education: '교육·수강', community: '지역·모임 활동', family_care: '가족 돌봄', certificate: '자격증',
}
export const NO_FILTERS = { sido: '', sigungu: '', hours: '', deadline_days: null }

const INIT = {
  screen: 'landing', step: 1, maxStep: 1,
  cards: [], cardSel: 0, activeCard: null,       // 카드: {id, card, competencies, card_in, question, removed, saved}
  types: ['job', 'part_time', 'certificate'], care: false,
  jobs: null, jobSel: 0, reasons: {},
  posts: null, postSel: null, filters: NO_FILTERS,
  gaps: null,
  msgs: [], chatRatio: 1 / 3, chatOpen: true,
  busy: null, err: null, typing: false, drawer: false, demo: false, meta: null, postsLoading: false,
}

function restore() {
  try {
    const v = JSON.parse(localStorage.getItem(KEY))
    if (!v) return INIT
    const reasons = Object.fromEntries(Object.entries(v.reasons || {}).filter(([, r]) => r.reason))   // 쓰던 중이던 이유는 버림
    return { ...INIT, ...v, reasons }
  } catch { return INIT }
}

let state = restore()
const subs = new Set()
export const get = () => state
export function set(p) {
  state = { ...state, ...(typeof p === 'function' ? p(state) : p) }
  subs.forEach(f => f())
  try {
    const o = { ...state }
    TRANSIENT.forEach(k => delete o[k])
    localStorage.setItem(KEY, JSON.stringify(o))
  } catch { /* 사생활 보호 창 등: 저장 없이 계속 */ }
}
export const useApp = () => useSyncExternalStore(cb => (subs.add(cb), () => subs.delete(cb)), get)

let n = 0
const uid = () => `${Date.now().toString(36)}${(n++).toString(36)}`
export const fmt = x => (x ?? 0).toLocaleString('ko-KR')

// ---------------- 대화창 ----------------
function say(t, x = {}) { set(p => ({ msgs: [...p.msgs, { id: uid(), r: 'a', t, step: p.step, ...x }] })) }
function you(t, kind) { set(p => ({ msgs: [...p.msgs, { id: uid(), r: 'u', t, step: p.step, kind }] })) }

async function typing(fn) {
  set({ typing: true })
  try { await fn() } catch (e) { say(e.message, { error: true }) } finally { set({ typing: false }) }
}

export function focusChat() {
  set({ chatOpen: true })
  setTimeout(() => document.getElementById('chat-input')?.focus(), 30)
}

const GREETING = '반가워요. 지금까지 해 오신 일을 편하게 들려주세요.\n어디서, 얼마나, 어떤 일을 하셨는지 한두 문장이면 충분해요. 직장 경력, 아르바이트, 자격증 모두 경험이에요.'

// ---------------- 경험 카드(① ② 인터뷰) ----------------
const card = id => state.cards.find(c => c.id === id)
const pending = c => !!c?.question && !c.question.end
const fromApi = (r, old = {}) => ({
  id: old.id || uid(), removed: old.removed || [], saved: old.saved || false,
  card: r.card, competencies: r.competencies, card_in: r.card_in, question: r.question,
})
function patchCard(id, x) {
  set(p => ({ cards: p.cards.map(c => c.id === id ? { ...c, ...(typeof x === 'function' ? x(c) : x) } : c) }))
}
// 카드가 바뀌면 그 뒤 단계 결과는 다시 계산해야 한다
function stale() { set(p => p.maxStep > 2 ? { maxStep: 2, jobs: null, posts: null, gaps: null } : {}) }

export function cardsIn() {
  const use = state.cards.some(c => c.saved) ? state.cards.filter(c => c.saved) : state.cards
  return use.map(c => ({ ...c.card_in, removed: c.removed }))   // 지운 역량은 서버가 카드와 엔진 추출 양쪽에서 뺀다
}

function ask(c, intro = '') {
  set({ activeCard: c.id })
  say((intro ? intro + '\n' : '') + c.question.question,
    { kind: 'interview', chips: [...(c.question.options || []), '잘 모르겠어요', '그만 물어봐도 돼요'] })
}

function askNextOrFinish(doneTitle) {
  const nxt = state.cards.find(pending)
  if (nxt) return ask(nxt, `이번에는 ‘${nxt.card.activity}’ 경험을 여쭤볼게요.`)
  set({ activeCard: null })
  const btn = state.step === 2 ? '직무 추천 받기' : '경험 카드 만들기'
  say((doneTitle ? `‘${doneTitle}’ 이야기는 잘 들었어요.\n` : '') +
    `더 생각나는 경험이 있으면 이어서 적어 주세요. 다 됐으면 아래 ‘${btn}’를 눌러 주세요.`)
}

async function startCards(text, opt = {}) {
  const r = await api('interview/start', { text, ...opt })
  const news = r.cards.map(x => fromApi(x))
  set(p => ({ cards: [...p.cards, ...news] }))
  stale()
  return news
}

async function answer(c, text) {
  const r = await api('interview/answer', { card: c.card, answer: text })
  patchCard(c.id, old => fromApi(r, old))
  stale()
  if (r.other_experience) {   // 지금 묻는 경험과 다른 이야기 → 새 카드로
    const news = await startCards(text)
    say(`다른 경험 같아서 ${news.map(x => `‘${x.card.activity}’`).join(', ')} 카드를 새로 만들었어요.`)
  }
  const now = card(c.id)
  if (pending(now)) ask(now)
  else askNextOrFinish(now.card.activity)
}

export function send(text) {
  text = text.trim()
  if (!text || state.typing) return
  if (state.screen === 'work' && state.step >= 3) {
    you(text, 'agent')
    return typing(agent)
  }
  you(text, 'interview')
  const c = card(state.activeCard)
  if (pending(c)) return typing(() => answer(c, text))
  return typing(async () => {
    const news = await startCards(text)
    const t = news.length > 1
      ? `경험 ${news.length}개로 나눠 카드 초안을 만들었어요: ${news.map(x => `‘${x.card.activity}’`).join(', ')}.`
      : news[0].card.activity === '내 경험' ? '말씀하신 경험으로 카드 초안을 만들었어요.' : `‘${news[0].card.activity}’ 경험으로 카드 초안을 만들었어요.`
    const first = news.find(pending)
    if (first) ask(first, t + (news.length > 1 ? `\n먼저 ‘${first.card.activity}’부터 여쭤볼게요.` : ''))
    else { say(t); askNextOrFinish() }
  })
}

// ② 화면에서 고친 칸 → 서버가 역량·등급을 다시 계산
export async function editField(id, field, value) {
  try {
    const r = await api('interview/edit', { card: card(id).card, field, value })
    patchCard(id, old => fromApi(r, old))
    stale()
  } catch (e) { say(e.message, { error: true }) }
}

const SLOT_Q = {
  role: '이 일에서 직접 맡으신 일은 무엇이었나요?', purpose: '이 일을 왜 하게 되셨나요? 무엇을 해결하거나 만들려고 했는지 궁금해요.',
  actions: '그 일을 하면서 구체적으로 어떤 작업을 하셨나요?', results: '그 결과 무엇이 달라졌나요? 숫자가 아니어도 괜찮아요.',
  period: '언제부터 언제까지 하셨나요? 대략이라도 괜찮아요.',
}
export function askSlot(id, slot) {
  if (state.typing) return
  const q = { slot, kind: 'basic', question: SLOT_Q[slot], options: [] }
  patchCard(id, c => ({ question: q, card: { ...c.card, last_question: q } }))
  focusChat()
  ask(card(id), `‘${card(id).card.activity}’ 카드의 빈칸을 여쭤볼게요.`)
}

export function removeComp(id, kw) { patchCard(id, c => ({ removed: [...c.removed, kw] })); stale() }
export function undoRemove(id) { patchCard(id, { removed: [] }); stale() }
export function saveCard(id) { patchCard(id, { saved: true }); stale() }

// ---------------- 단계 이동과 ③ ④ ⑤ ----------------
export function start() {
  set(p => ({ screen: 'work', step: Math.min(p.step, p.maxStep) }))
  if (!state.msgs.length) say(GREETING)
}
export function goStep(k) { if (k <= state.maxStep) set({ screen: 'work', step: k, err: null }) }

async function load(step, title, sub, fn) {
  set({ busy: { step, title, sub }, err: null, screen: 'work', step })
  try {
    await fn()
    set({ busy: null })
  } catch (e) {
    set({ busy: null, err: { step, title: ERR_TITLE[step], sub: e.message, retry: () => load(step, title, sub, fn) } })
  }
}
const ERR_TITLE = { 2: '경험 카드를 만들지 못했어요', 3: '직무를 찾지 못했어요', 4: '채용공고를 불러오지 못했어요', 5: '교육과정을 불러오지 못했어요' }

export function toCards() {
  set(p => ({ screen: 'work', step: 2, maxStep: Math.max(p.maxStep, 2), cardSel: 0 }))
  const k = state.cards.length
  if (k) say(`경험 카드 초안 ${k}장을 만들었어요. 틀린 곳은 바로 고치고, 맞으면 저장해 주세요.`)
}

export function recommend() {
  if (state.maxStep >= 3 && state.jobs) return goStep(3)
  if (!state.cards.some(c => c.saved)) set(p => ({ cards: p.cards.map(c => ({ ...c, saved: true })) }))
  const m = state.meta
  return load(3, `직무 ${m ? fmt(m.occupations) + '개' : '정보'}와 비교하는 중이에요`, '내 역량과 각 직무가 하는 일을 견주고 있어요.', async () => {
    const r = await api('recommend', { cards: cardsIn() })
    set({ jobs: r.jobs, jobSel: 0, reasons: {}, posts: null, gaps: null, maxStep: 3 })
    const j = r.jobs[0]
    if (!j) return say('경험 카드로 맞는 직무를 찾지 못했어요. 하신 일을 조금 더 자세히 들려주시면 다시 찾아볼게요.')
    say(`저장한 경험 카드 ${cardsIn().length}장으로 직무를 찾았어요.\n‘${j.name}’ 직무가 ${j.score.toFixed(1)}점으로 1위예요. 점수는 경험과 직무가 겹치는 정도이고, 합격 가능성은 아니에요.`,
      { chips: ['점수가 어떻게 나온 거예요?', '다른 직무도 궁금해요'] })
    explain(0)
  })
}

export async function explain(i) {
  const j = state.jobs?.[i]
  const cur = j && state.reasons[j.occupation_id]
  if (!j || (cur && !cur.error)) return
  set(p => ({ reasons: { ...p.reasons, [j.occupation_id]: { loading: true } } }))
  let r
  try { r = await api('explain', { job: j }) } catch { r = { error: true } }
  set(p => ({ reasons: { ...p.reasons, [j.occupation_id]: r } }))
}

export function pickJob(i) {
  if (i !== state.jobSel) set(p => ({ jobSel: i, ...(p.maxStep > 3 ? { maxStep: 3, posts: null, gaps: null } : {}) }))
  explain(i)
}

const cleanFilters = f => Object.fromEntries(Object.entries(f).filter(([, v]) => v !== '' && v !== null))

export function postings() {
  if (state.maxStep >= 4 && state.posts) return goStep(4)
  const j = state.jobs[state.jobSel], m = state.meta
  return load(4, `공고 ${m ? fmt(m.postings) + '건' : ''}에서 찾는 중이에요`, `‘${j.name}’ 공고를 내 역량과 맞춰 보고 있어요.`, async () => {
    await fetchPosts(state.filters)
    say(`‘${j.name}’ 공고 ${fmt(state.posts.total)}건을 찾았어요. 내 역량과 많이 겹치는 공고부터 보여 드려요.\n지역이나 근무시간 조건은 위쪽에서 바꿀 수 있어요.`)
  })
}

async function fetchPosts(filters) {
  const j = state.jobs[state.jobSel]
  const r = await api('postings', { cards: cardsIn(), occupation_id: j.occupation_id, filters: cleanFilters(filters), limit: 12 })
  set({ posts: r, postSel: r.postings[0]?.posting_id || null, filters, maxStep: 4, gaps: null })
}

export async function setFilters(f) {
  const filters = { ...state.filters, ...f }
  set({ postsLoading: true, filters })
  try { await fetchPosts(filters) } catch (e) {
    set({ err: { step: 4, title: ERR_TITLE[4], sub: e.message, retry: () => { set({ err: null }); setFilters({}) } } })
  } finally { set({ postsLoading: false }) }
}

export function pickPost(id) { set(p => ({ postSel: id, ...(p.maxStep > 4 ? { maxStep: 4, gaps: null } : {}) })) }

export const selectedPost = s => s.posts?.postings.find(p => p.posting_id === s.postSel) || null

export function courses() {
  if (state.maxStep >= 5 && state.gaps) return goStep(5)
  const j = state.jobs[state.jobSel], m = state.meta
  return load(5, `국비 교육과정 ${m ? fmt(m.courses) + '개' : ''}에서 찾는 중이에요`, '부족한 역량을 채울 과정을 찾고 있어요.', async () => {
    const r = await api('courses', { cards: cardsIn(), occupation_id: j.occupation_id, posting_id: state.postSel || undefined })
    set({ gaps: r.gaps, maxStep: 5 })
    const withC = r.gaps.filter(g => g.courses.length)
    say(r.gaps.length
      ? `채우면 좋은 역량 ${r.gaps.length}가지를 찾았어요. 그중 ${withC.length}가지는 지금 신청할 수 있는 국비 과정이 있어요.`
      : '교육으로 채울 핵심 역량이 없어요. 고른 공고의 역량을 이미 갖고 계세요.')
  })
}

// ---------------- 대화창 에이전트(③ ④ ⑤) ----------------
async function agent() {
  const s = state
  const hist = []
  for (const m of s.msgs.filter(x => x.kind === 'agent').slice(-20)) {
    const role = m.r === 'u' ? 'user' : 'assistant', text = m.t.slice(0, 3500)
    if (hist.length && hist.at(-1).role === role) hist.at(-1).text += '\n' + text   // Bedrock은 역할이 번갈아야 함
    else hist.push({ role, text })
  }
  while (hist.length && hist[0].role !== 'user') hist.shift()
  const job = s.jobs?.[s.jobSel]
  const r = await api('chat', {
    messages: hist, step: STEP_LABEL[s.step], cards: cardsIn(),
    occupation_id: job?.occupation_id, posting_id: s.step >= 4 ? s.postSel || undefined : undefined,
  })
  say(r.reply || '답을 만들지 못했어요. 다시 물어봐 주세요.', r.error ? { error: true } : { kind: 'agent' })
}

// ---------------- 시연 도구 ----------------
export const PERSONAS = [   // 로직팀 시뮬레이션 인물(시험의 PARK·CHOI와 같은 글). 시연 인물(TEAM W2)이 오면 바꾼다
  { name: '박물류', desc: '물류센터 지게차 10년 · 시뮬레이션 인물', cards: [
    { title: '물류센터 근무', type: 'job', text: '물류센터에서 10년 동안 지게차로 상하차와 운반을 했습니다. 입고 검수와 재고 관리도 맡았습니다.' },
    { title: '자격증', type: 'certificate', text: '지게차운전기능사 자격증과 1종 보통 운전면허를 보유하고 있습니다.' }] },
  { name: '최경리', desc: '회사 경리 5년 · 시뮬레이션 인물', cards: [
    { title: '회사 경리 업무', type: 'job', text: '회사에서 5년 동안 경리 업무를 했습니다. 엑셀로 급여와 회계 장부를 정리하고 세금계산서를 발행했습니다. 거래처 전화 응대도 담당했습니다.' },
    { title: '자격증', type: 'certificate', text: '컴퓨터활용능력 2급 자격증을 취득했습니다.' }] },
]

export function reset(extra = {}) {
  try { localStorage.removeItem(KEY) } catch { /* 없음 */ }
  set({ ...INIT, meta: state.meta, ...extra })
}

export function loadPersona(p) {
  reset({ demo: true, msgs: [{ id: uid(), r: 'a', t: GREETING, step: 1 }] })
  return load(2, '예시 인물의 경험을 정리하는 중이에요', `${p.name} 님의 경험 글 ${p.cards.length}개를 카드로 만들고 있어요.`, async () => {
    const cards = []
    for (const c of p.cards) cards.push(...(await api('interview/start', c)).cards.map(x => ({ ...fromApi(x), saved: true })))
    set({ cards, maxStep: 2, cardSel: 0 })
    say(`예시 인물 ‘${p.name}’ 님의 경험 카드 ${cards.length}장을 불러와 저장해 두었어요.`)
  })
}
