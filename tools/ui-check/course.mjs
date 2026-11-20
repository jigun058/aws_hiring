// 수료 과정 규칙(B25, P3 4.2): 고용24 과정명과 맞는 수료 이야기 → 그 과정의 역량이 카드에 '수료 과정: …'으로 붙는지
import { open } from './lib.mjs'
const { p, shot, idle, state, close } = await open('course')
await p.getByText('시작하기').first().click(); await p.waitForTimeout(500)
await p.locator('#chat-input').fill('작년에 요양보호사 자격취득과정을 수료했어요.'); await p.locator('#chat-input').press('Enter'); await idle()
await p.getByRole('button', { name: '경험 카드 만들기 →' }).click(); await p.waitForTimeout(600)
const card = p.locator('main'); const n = await p.getByText(/수료 과정:/).count()
await p.getByText(/수료 과정:/).first().scrollIntoViewIfNeeded(); await shot('1-card')
console.log('수료 과정 표시:', n, '카드 유형:', (await state()).cards[0].card.type, '/', (await state()).cards[0].card.activity)
console.log((await state()).cards[0].competencies.map(k => `${k.keyword}(${k.level}${k.match === 'course' ? ', 과정' : ''})`).join(', '))
await close()
