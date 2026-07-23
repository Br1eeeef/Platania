const fs = require('node:fs')
const path = require('node:path')
const { chromium } = require(path.resolve(__dirname, '..', 'web', 'node_modules', 'playwright-core'))

const baseURL = process.env.PLATANIA_BASE_URL || 'http://127.0.0.1:8010'
const executablePath = process.env.PLATANIA_BROWSER_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const outputDir = path.resolve(process.env.PLATANIA_BROWSER_OUTPUT || path.join(__dirname, '..', '.artifacts', 'browser'))

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

async function assertNoOverflow(page, label) {
  const dimensions = await page.evaluate(() => ({ width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth }))
  assert(dimensions.scrollWidth <= dimensions.width + 1, `${label} has horizontal overflow: ${JSON.stringify(dimensions)}`)
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true })
  const browser = await chromium.launch({ executablePath, headless: true })
  const errors = []
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 })
  const page = await desktop.newPage()
  page.on('console', (message) => { if (message.type() === 'error') errors.push(`console: ${message.text()}`) })
  page.on('pageerror', (error) => errors.push(`page: ${error.message}`))

  await page.goto(`${baseURL}/welcome`, { waitUntil: 'networkidle' })
  await page.getByRole('link', { name: /申请会员/ }).waitFor()
  assert(await page.getByText('联系 Br1ef', { exact: true }).count() >= 1, 'welcome contact CTA missing')
  assert(await page.getByText('已有账号登录', { exact: true }).count() >= 1, 'welcome login CTA missing')
  assert(await page.getByText('登录 / 注册', { exact: true }).count() === 0, 'public registration text is still visible')
  await assertNoOverflow(page, 'desktop welcome')
  await page.screenshot({ path: path.join(outputDir, 'desktop-welcome.png'), fullPage: true })

  await page.goto(`${baseURL}/stocks/600519.SH`, { waitUntil: 'networkidle' })
  await page.getByRole('heading', { name: '贵州茅台' }).waitFor()
  const canvasInfo = await page.locator('canvas').evaluateAll((canvases) => canvases.map((canvas) => {
    const context = canvas.getContext('2d')
    if (!context || !canvas.width || !canvas.height) return { width: canvas.width, height: canvas.height, painted: false }
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data
    let painted = false
    for (let index = 3; index < pixels.length; index += Math.max(4, Math.floor(pixels.length / 2000 / 4) * 4)) {
      if (pixels[index] > 0) { painted = true; break }
    }
    return { width: canvas.width, height: canvas.height, painted }
  }))
  assert(canvasInfo.some((item) => item.width > 200 && item.height > 100 && item.painted), `K-line canvas is blank: ${JSON.stringify(canvasInfo)}`)
  await page.getByRole('button', { name: '周K' }).click()
  await page.waitForLoadState('networkidle')
  assert(await page.getByRole('button', { name: '周K' }).getAttribute('class') === 'active', 'weekly K switch did not activate')
  await page.getByRole('button', { name: '5分', exact: true }).click()
  await page.waitForLoadState('networkidle')
  assert(await page.getByRole('button', { name: '5分', exact: true }).getAttribute('class') === 'active', '5-minute K switch did not activate')
  assert(await page.getByText('真实数据', { exact: false }).count() >= 1, 'live-data badge is missing after the 5-minute switch')
  await assertNoOverflow(page, 'desktop stock')
  await page.screenshot({ path: path.join(outputDir, 'desktop-stock.png'), fullPage: true })

  await page.goto(`${baseURL}/ai-workshop`, { waitUntil: 'networkidle' })
  await page.getByRole('button', { name: /生成受约束策略/ }).click()
  await page.getByText('已校验', { exact: true }).waitFor()
  await page.getByRole('button', { name: /用招商银行演示回测/ }).click()
  await page.getByRole('heading', { name: '回测报告' }).waitFor()

  await page.goto(`${baseURL}/admin/members/new`, { waitUntil: 'networkidle' })
  await page.getByLabel('会员邮箱').fill('browser-check@example.com')
  await page.getByLabel('付款备注').fill('浏览器验收付款确认')
  await page.getByLabel('我已在线下确认收到付款').check()
  await page.getByRole('button', { name: /确认并发送 Supabase 邀请/ }).click()
  await page.getByText(/邀请已发送/).waitFor()
  await page.screenshot({ path: path.join(outputDir, 'desktop-admin.png'), fullPage: true })

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 })
  const mobilePage = await mobile.newPage()
  mobilePage.on('console', (message) => { if (message.type() === 'error') errors.push(`mobile console: ${message.text()}`) })
  mobilePage.on('pageerror', (error) => errors.push(`mobile page: ${error.message}`))
  await mobilePage.goto(`${baseURL}/stocks/600519.SH`, { waitUntil: 'networkidle' })
  await mobilePage.getByRole('navigation', { name: '移动端主导航' }).waitFor()
  assert(await mobilePage.getByRole('navigation', { name: '移动端主导航' }).isVisible(), 'mobile bottom navigation is hidden')
  await assertNoOverflow(mobilePage, 'mobile stock')
  await mobilePage.screenshot({ path: path.join(outputDir, 'mobile-stock.png'), fullPage: true })

  await desktop.close()
  await mobile.close()
  await browser.close()
  assert(errors.length === 0, `browser errors detected:\n${errors.join('\n')}`)
  process.stdout.write(`${JSON.stringify({ ok: true, baseURL, screenshots: outputDir, canvasInfo, errors }, null, 2)}\n`)
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`)
  process.exitCode = 1
})
