// 예시 답 여러 개 골라 보내기(11/20 팀 요청): 두 개를 고르면 "고른 답 2개 보내기"로 한 번에 간다. 대화창을 닫았다 열어도 오류 없음
import { open, msgsText } from './lib.mjs'
const { p, shot, idle, state, close } = await open('chips')
await p.getByText('시작하기').first().click(); await p.waitForTimeout(500)
await p.locator('#chat-input').fill('동네 마트에서 5년 동안 일했어요.'); await p.locator('#chat-input').press('Enter'); await idle()
const st0 = await state(), q = st0.cards[0].question
console.log('질문:', q.slot, q.options)
await p.getByRole('button', { name: q.options[0], exact: true }).click()
await p.getByRole('button', { name: q.options[1], exact: true }).click(); await shot('1-picked')
console.log('보내기 버튼:', await p.getByRole('button', { name: /고른 답 \d개 보내기/ }).innerText())
await p.getByRole('button', { name: /고른 답 \d개 보내기/ }).click(); await idle(); await shot('2-sent')
await p.getByRole('button', { name: /대화창 접기/ }).click(); await p.getByText('AI 대화창 열기').click(); await shot('3-reopen')
const st = await state()
console.log('보낸 답:', st.msgs.filter(m => m.r === 'u').at(-1).t)
console.log(`${q.slot} 칸:`, JSON.stringify(st.cards[0].card.slots[q.slot]))
await close()
