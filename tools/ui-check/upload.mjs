// 이력서 PDF + 자격증 사진 + 못 읽는 hwp를 올리고, 합치기 제안이 뜨면 합친다. 사진 읽기는 LIVE=1(또는 배포 주소)에서만 됨
import { writeFileSync } from 'fs'
import { open, ROOT, cardsText, msgsText } from './lib.mjs'
const { p, out, shot, idle, state, close } = await open('upload')
const cert = await p.context().browser().newPage()
await cert.setViewportSize({ width: 900, height: 600 })
await cert.setContent(`<div style="font-family:sans-serif;border:8px double #446;margin:20px;padding:40px;text-align:center"><h1>국가기술자격증</h1>
<p style="font-size:22px">자격종목: 지게차운전기능사</p><p style="font-size:20px">성명: 박물류</p><p>취득일: 2014년 5월 20일</p><p>한국산업인력공단 이사장</p></div>`)
await cert.screenshot({ path: `${out}/cert.png` }); await cert.close()
writeFileSync(`${out}/memo.hwp`, 'x')
await p.getByText('시작하기').first().click(); await p.waitForTimeout(500)
await p.locator('input[type=file]').setInputFiles([ROOT + 'backend/tests/fixtures/resume.pdf', `${out}/cert.png`, `${out}/memo.hwp`])
await idle(120000); await shot('1-read')
const merge = p.getByRole('button', { name: '한 장으로 합치기' }).first()
if (await merge.count()) { await merge.click(); await p.waitForTimeout(300); await idle(); await shot('2-merged') } else console.log('합치기 제안 없음')
const st = await state()
console.log(cardsText(st)); console.log('---\n' + msgsText(st))
await close()
