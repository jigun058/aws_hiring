// 공통 준비: BASE가 localhost면 서버를 직접 띄우고(LIVE=1이면 실제 Bedrock, 아니면 규칙 대체), 아니면 그 주소를 연다.
import { chromium } from 'playwright'
import { spawn } from 'child_process'
import { mkdirSync } from 'fs'
import { fileURLToPath } from 'url'

export const ROOT = fileURLToPath(new URL('../../', import.meta.url))
export const BASE = process.env.BASE || 'http://localhost:8000'
export const LIVE = process.env.LIVE === '1'

export async function open(name, { width = 1280, height = 800 } = {}) {
  let srv = null
  if (BASE.includes('localhost')) {
    const env = LIVE ? { AWS_PROFILE: process.env.AWS_PROFILE || 'tae' } : { AWS_PROFILE: 'none-offline', AWS_EC2_METADATA_DISABLED: 'true' }
    srv = spawn(ROOT + '.venv/bin/uvicorn', ['careerlens.api:app', '--port', '8000'], { cwd: ROOT + 'backend', env: { ...process.env, ...env }, stdio: 'ignore' })
    process.on('exit', () => srv.kill())  // 스크립트가 중간에 죽어도 서버를 남기지 않게
    let up = false
    for (let i = 0; i < 60 && !up; i++) { try { up = (await fetch(BASE + '/api/health')).ok } catch {} if (!up) await new Promise(r => setTimeout(r, 500)) }
    if (!up) { srv.kill(); throw new Error('서버가 30초 안에 뜨지 않음 (8000번을 이미 쓰는 서버가 있는지 확인)') }
  }
  const out = `${ROOT}tools/ui-check/shots/${name}`
  mkdirSync(out, { recursive: true })
  const browser = await chromium.launch()
  const p = await browser.newPage({ viewport: { width, height } })
  const errs = []
  p.on('pageerror', e => errs.push('pageerror ' + e.message))
  p.on('console', m => m.type() === 'error' && errs.push('console ' + m.text()))
  p.on('dialog', d => d.accept())
  await p.goto(BASE + '/'); await p.evaluate(() => localStorage.clear()); await p.reload()
  return {
    p, out,
    shot: async n => { await p.waitForTimeout(400); await p.screenshot({ path: `${out}/${width}-${n}.png` }) },
    idle: (timeout = 90000) => p.waitForFunction(() => !document.querySelector('[role=status]'), null, { timeout }),
    state: () => p.evaluate(() => JSON.parse(localStorage.getItem('careerlens-v1'))),
    persona: async name => {
      await p.getByTitle('시연 도구').click(); await p.getByRole('button', { name }).click()
      await p.waitForFunction(() => !document.querySelector('[role=status]'), null, { timeout: 90000 })
      await p.getByTitle('시연 도구').click()
    },
    close: async () => { console.log(errs.join('\n') || 'no page errors'); console.log('screenshots:', out); await browser.close(); srv?.kill() },
  }
}

export const cardsText = st => st.cards.map(c => `${c.card.type} | ${c.card.activity} | made_by=${c.card.made_by} | ${c.competencies.map(k => `${k.keyword}${k.match === 'llm_choice' ? '(AI후보)' : ''}`).join(', ')}`).join('\n')
export const msgsText = st => st.msgs.map(m => `${m.r}: ${m.t}`).join('\n')
