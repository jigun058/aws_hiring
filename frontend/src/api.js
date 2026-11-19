// 서버 호출 한 곳. 실패하면 사람이 읽을 수 있는 문장을 담은 Error를 던진다(화면 품질 기준 3).

// 시연 녹화·재생(DESIGN 6절, BACKLOG B29): 녹화 중엔 요청과 응답을 쌓고, 재생 중엔 서버 대신 녹화본으로 답한다.
// 앱 상태(careerlens-v1)와 따로 두어 "처음부터 다시 시작"해도 남는다.
const TKEY = 'careerlens-tape'
let tape = { mode: 'off', calls: [] }
try { tape = JSON.parse(localStorage.getItem(TKEY)) || tape } catch { /* 저장소 없음 */ }
let used = new Set()

function saveTape() {
  try { localStorage.setItem(TKEY, JSON.stringify(tape)) } catch { /* 가득 참 등: 이 탭 메모리에만 */ }
}
export const tapeInfo = () => ({ mode: tape.mode, n: tape.calls.length })
export const tapeJson = () => JSON.stringify(tape.calls)
export function setTape(mode, calls) {
  tape = { mode, calls: calls ?? (mode === 'rec' ? [] : tape.calls) }
  used = new Set()
  saveTape()
}

// 똑같은 요청이 녹화돼 있으면 그 답, 없으면 같은 API의 아직 안 쓴 다음 답(입력 글이 조금 달라도 이어지게)
function pick(calls, used, path, key) {
  let i = calls.findIndex(c => c.path === path && c.key === key)
  if (i < 0) i = calls.findIndex((c, k) => !used.has(k) && c.path === path)
  if (i >= 0) used.add(i)
  return i
}

export async function api(path, body) {
  const key = JSON.stringify(body ?? null)
  if (tape.mode === 'play') {
    const i = pick(tape.calls, used, path, key)
    if (i >= 0) {   // 없으면 실제 서버로
      const c = tape.calls[i]
      await new Promise(r => setTimeout(r, Math.min(c.ms, 2500)))
      return structuredClone(c.res)
    }
  }
  const t0 = Date.now()
  let r
  try {
    r = await fetch('/api/' + path, body === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
  } catch {
    throw new Error('인터넷 연결이 잠시 끊긴 것 같아요. 연결을 확인하고 다시 시도해 주세요.')
  }
  if (!r.ok) {
    let d = null
    try { d = (await r.json()).detail } catch { /* 본문 없음 */ }
    throw new Error(typeof d === 'string' ? d : '서버가 잠시 답하지 않아요. 1~2분 뒤에 다시 시도해 주세요.')
  }
  const res = await r.json()
  if (tape.mode === 'rec') { tape.calls.push({ path, key, ms: Date.now() - t0, res }); saveTape() }
  return res
}
