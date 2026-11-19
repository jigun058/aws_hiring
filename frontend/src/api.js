// 서버 호출 한 곳. 실패하면 사람이 읽을 수 있는 문장을 담은 Error를 던진다(화면 품질 기준 3).
export async function api(path, body) {
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
  return r.json()
}
