const fs = require('node:fs')
const path = require('node:path')
const { chromium } = require(path.resolve(__dirname, '..', 'web', 'node_modules', 'playwright-core'))

const baseURL = process.env.PLATANIA_BASE_URL || 'http://127.0.0.1:8014'
const executablePath = process.env.PLATANIA_BROWSER_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const outputDir = path.resolve(__dirname, '..', '.artifacts', 'browser')

function assert(condition, message) { if (!condition) throw new Error(message) }

async function noOverflow(page, label) {
  const sizes = await page.evaluate(() => ({ viewport: window.innerWidth, content: document.documentElement.scrollWidth }))
  assert(sizes.content <= sizes.viewport + 1, `${label} has horizontal overflow: ${JSON.stringify(sizes)}`)
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true })
  const browser = await chromium.launch({ executablePath, headless: true })
  const errors = []
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  desktop.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
  desktop.on('pageerror', (error) => errors.push(error.message))
  await desktop.goto(`${baseURL}/backtests/new?symbol=600519.SH&strategy=trend_momentum`, { waitUntil: 'domcontentloaded' })
  await desktop.getByRole('heading', { name: '可配置回测工作台' }).waitFor()
  await desktop.getByLabel('初始资金（元）').fill('250000')
  await desktop.getByLabel('最大仓位（%）').fill('35')
  await desktop.getByLabel('RSI 下限').fill('45')
  const responsePromise = desktop.waitForResponse((response) => response.url().includes('/api/backtests') && response.request().method() === 'POST')
  await desktop.getByRole('button', { name: '运行回测', exact: true }).click()
  const response = await responsePromise
  assert(response.status() === 201, `backtest API returned ${response.status()}`)
  await desktop.getByRole('heading', { name: '回测报告' }).waitFor()
  await desktop.getByRole('heading', { name: '参数快照' }).waitFor()
  assert(await desktop.getByText(/250,000/).count() >= 1, 'custom initial cash is missing from report')
  assert(await desktop.getByText(/rsi_min: 45/).count() >= 1, 'custom strategy parameter is missing from report')
  await noOverflow(desktop, 'desktop backtest report')
  await desktop.screenshot({ path: path.join(outputDir, 'backtest-workbench-report.png'), fullPage: true })

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } })
  await mobile.goto(`${baseURL}/backtests/new?symbol=600519.SH`, { waitUntil: 'domcontentloaded' })
  await mobile.getByRole('heading', { name: '可配置回测工作台' }).waitFor()
  await noOverflow(mobile, 'mobile backtest workbench')
  await mobile.screenshot({ path: path.join(outputDir, 'backtest-workbench-mobile.png'), fullPage: true })
  await browser.close()
  assert(errors.length === 0, `browser console errors: ${errors.join('; ')}`)
  process.stdout.write(JSON.stringify({ ok: true, screenshots: outputDir }) + '\n')
}

main().catch((error) => { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1 })
