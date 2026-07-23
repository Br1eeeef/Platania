const fs = require('node:fs')
const path = require('node:path')
const { chromium } = require(path.resolve(__dirname, '..', 'web', 'node_modules', 'playwright-core'))

const baseURL = process.env.PLATANIA_BASE_URL || 'http://127.0.0.1:8011'
const executablePath = process.env.PLATANIA_BROWSER_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const outputDir = path.resolve(__dirname, '..', '.artifacts', 'browser')

function assert(condition, message) { if (!condition) throw new Error(message) }

async function assertNoOverflow(page, label) {
  const metrics = await page.evaluate(() => ({ width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth }))
  assert(metrics.scrollWidth <= metrics.width + 1, `${label} has horizontal overflow: ${JSON.stringify(metrics)}`)
}

async function verifyStock(page, mobile = false) {
  const errors = []
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto(`${baseURL}/stocks/600519.SH`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('heading', { name: '贵州茅台' }).waitFor()
  const fiveMinuteResponse = page.waitForResponse((response) => response.url().includes('/bars?period=5m') && response.status() === 200)
  await page.getByRole('button', { name: '5分', exact: true }).click()
  await fiveMinuteResponse
  await page.getByRole('button', { name: '5分', exact: true }).waitFor()
  assert(await page.getByRole('button', { name: '5分', exact: true }).getAttribute('class') === 'active', '5-minute K switch did not activate')
  assert(await page.locator('canvas').count() > 0, 'K-line canvas was not rendered')
  assert(await page.getByText('真实缓存', { exact: false }).count() >= 1, 'live-data badge is missing')
  if (mobile) await page.getByRole('navigation', { name: '移动端主导航' }).waitFor()
  await assertNoOverflow(page, mobile ? 'mobile stock' : 'desktop stock')
  assert(errors.length === 0, `browser console errors: ${errors.join('; ')}`)
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true })
  const browser = await chromium.launch({ executablePath, headless: true })
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  await verifyStock(desktop)
  await desktop.screenshot({ path: path.join(outputDir, 'realtime-desktop-stock.png'), fullPage: true })
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } })
  await verifyStock(mobile, true)
  await mobile.screenshot({ path: path.join(outputDir, 'realtime-mobile-stock.png'), fullPage: true })
  await browser.close()
  process.stdout.write(JSON.stringify({ ok: true, baseURL, screenshots: outputDir }) + '\n')
}

main().catch((error) => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1 })
