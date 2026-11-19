// 대화창 답이 흘러나오는지: 0.25초마다 상태 문구와 마지막 메시지 글자 수를 찍는다(B27). LIVE=1 또는 배포 주소
import { open } from './lib.mjs'
const { p, shot, idle, persona, close } = await open('stream')
await persona(/박물류/)
await p.getByRole('button', { name: '직무 추천 받기 →' }).click(); await idle(); await p.waitForTimeout(500)
await p.locator('#chat-input').fill('서울에 있는 지게차 공고 3개만 알려줘')
const t0 = Date.now(); await p.getByRole('button', { name: '보내기 ↑' }).click()
const marks = []
for (let i = 0; i < 120; i++) {
  await p.waitForTimeout(250)
  const s = await p.evaluate(() => ({ status: document.querySelector('[role=status]')?.innerText || '', last: JSON.parse(localStorage.getItem('careerlens-v1')).msgs.at(-1) }))
  const m = `${s.status.slice(0, 30)} | ${s.last.r}:${s.last.t.length}`
  if (marks.at(-1)?.m !== m) marks.push({ at: ((Date.now() - t0) / 1000).toFixed(1), m })
  if (i === 14) await shot('mid')
  if (!s.status) break
}
await shot('end')
console.log(marks.map(x => `${x.at}s ${x.m}`).join('\n'))
await close()
