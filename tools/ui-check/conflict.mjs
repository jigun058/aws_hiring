// 자료·진술 불일치 질문(B22, P3 5.3 ③): 이력서 글(2015~2020)을 올리고 대화로 다른 기간(2017~2020)을 말하면
// "어느 쪽이 맞나요?"가 나오고, 선택지를 누르면 카드 기간이 그 값이 되는지. 파일에서 기간을 뽑는 것은 AI라 LIVE=1(또는 배포 주소)에서만 됨
import { writeFileSync } from 'fs'
import { open, msgsText } from './lib.mjs'
const { p, out, shot, idle, state, close } = await open('conflict-' + (process.env.CASE || 'period'))
// CASE=period(기본)|role|result: 같은 이력서 글에 대해 대화로 다르게 말할 내용
const CASES = {
  period: '사실 2017년부터 2020년까지 다녔어요. 직원은 5명이었어요.',
  role: '사실 저는 경리가 아니라 영업 관리 담당이었어요. 직원은 5명이었어요.',
  result: '거래처 미수금 오류는 30% 정도 줄었어요. 직원은 5명이었어요.',
}
const CASE = process.env.CASE || 'period'
writeFileSync(`${out}/resume.txt`, '○○상사 경리 담당 (2015년 3월 ~ 2020년 2월)\n장부와 급여를 엑셀로 정리했습니다.\n거래처 미수금 오류를 20% 줄였습니다.\n')
await p.getByText('시작하기').first().click(); await p.waitForTimeout(500)
await p.locator('input[type=file]').setInputFiles(`${out}/resume.txt`)
await idle(120000); await shot('1-read')
const cur = async () => { const st = await state(); return st.cards.find(c => c.id === st.activeCard) }
const say = async t => { await p.locator('#chat-input').fill(t); await p.locator('#chat-input').press('Enter'); await p.waitForTimeout(300); await idle() }
let c = await cur()
console.log('CASE', CASE, '파일 카드:', JSON.stringify({ role: c?.card.slots.role?.value, period: c?.card.slots.period?.value, results: c?.card.slots.results.map(x => x.value) }), '\n첫 질문:', c?.question)
await say(CASES[CASE])
let asked = null
for (let i = 0; i < 6 && (c = await cur()); i++) {
  if (c.question?.kind === 'conflict') { asked = c.question; break }
  await say('잘 모르겠어요')
}
await shot('2-question')
if (!asked) console.log('불일치 질문 안 나옴. conflicts =', JSON.stringify((await state()).cards.map(x => x.card.conflicts)))
else {
  console.log('불일치 질문:', asked.question, asked.options)
  await p.getByRole('button', { name: asked.options[1], exact: true }).click(); await p.waitForTimeout(300); await idle()
  await shot('3-picked')
  const st = await state()
  console.log('고른 뒤:', JSON.stringify(st.cards.map(x => ({ role: x.card.slots.role?.value, period: x.card.slots.period?.value, results: x.card.slots.results.map(r => r.value) }))), '상태:', st.cards.map(x => x.card.conflicts?.map(k => k.status)))
}
console.log('---\n' + msgsText(await state()))
await close()
