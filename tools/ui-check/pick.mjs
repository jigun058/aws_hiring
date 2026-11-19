// 규칙이 못 잡는 문장에서 AI가 사전 후보를 고르는지(B24). LIVE=1(또는 배포 주소)에서만 의미가 있다
import { open, cardsText } from './lib.mjs'
const { p, shot, idle, state, close } = await open('pick', { height: 900 })
await p.getByText('시작하기').first().click(); await p.waitForTimeout(400)
await p.locator('#chat-input').fill('동네 미용실에서 5년 일했어요. 손님들 머리를 자르고 염색을 해 드렸어요. 단골 손님이 30명 넘게 생겼어요.')
await p.getByRole('button', { name: '보내기 ↑' }).click(); await p.waitForTimeout(500); await idle()
await p.getByRole('button', { name: '경험 카드 만들기 →' }).click(); await p.waitForTimeout(800)
const t = p.getByText('AI가 고른 후보').first()
if (await t.count()) { await t.scrollIntoViewIfNeeded(); await p.getByRole('button', { name: '근거 보기 ▾' }).first().click().catch(() => {}) } else console.log('AI 후보 표시 없음')
await shot('card')
console.log(cardsText(await state()))
await close()
