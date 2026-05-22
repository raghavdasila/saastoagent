import { spawn } from 'node:child_process'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { chromium, expect } from '@playwright/test'

const appUrl = process.env.E2E_APP_URL || 'http://localhost:3007'
const fixtureLocalUrl = process.env.E2E_FIXTURE_LOCAL_URL || 'http://localhost:9109'
const fixtureDockerUrl = process.env.E2E_STOREFRONT_BASE_URL || 'http://host.docker.internal:9109'
const artifactRoot =
  process.env.SAASTOAGENT_E2E_ARTIFACT_DIR ||
  path.join(os.tmpdir(), `saastoagent-ui-e2e-${Date.now()}`)
const forbiddenPublicLeaks = [
  'listproducts',
  'getproduct',
  'createproduct',
  '/products/{',
  '/admin/products',
  'score',
  'trace',
  'tool_start',
  'tool_end',
  'operationid',
]

const __dirname = path.dirname(fileURLToPath(import.meta.url))
let fixtureProcess = null

async function main() {
  await fs.mkdir(artifactRoot, { recursive: true })
  await ensureFixture()
  await postJson(`${fixtureLocalUrl}/__fixture/reset`, {})
  await requireOk(`${appUrl}/api/health`)

  const runId = Date.now()
  const email = `ui-e2e-${runId}@example.com`
  const password = 'SaaStoAgent123!'
  const slug = `ui-e2e-${runId}`
  const evidence = {
    artifactRoot,
    email,
    slug,
    appUrl,
    fixtureDockerUrl,
    screenshots: [],
  }

  const browser = await chromium.launch({ headless: process.env.E2E_HEADLESS !== '0' })
  const owner = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await owner.newPage()

  try {
    await page.goto(`${appUrl}/register`)
    await page.getByTestId('corpus-auth-display-name').fill('UI E2E Owner')
    await page.getByTestId('corpus-auth-email').fill(email)
    await page.getByTestId('corpus-auth-password').fill(password)
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page.getByTestId('auth-user-pill')).toContainText(email)

    await page.getByRole('button', { name: /Create Agent/ }).first().click()
    const createAgentProposal = page.getByTestId('corpus-proposal-surface')
    await expect(createAgentProposal).toBeVisible()
    await createAgentProposal.locator('input').nth(0).fill(`UI E2E ${runId}`)
    await createAgentProposal.locator('input').nth(1).fill(slug)
    await createAgentProposal.getByRole('button', { name: /Continue|Create SaaS Agent/ }).click()
    await expect(page).toHaveURL(/\/app\/agents\//, { timeout: 15000 })

    await page.getByPlaceholder('Message Corpus').fill('let me setup the api')
    await page.keyboard.press('Enter')
    await expect(page.getByTestId('connection-setup-surface')).toBeVisible({ timeout: 15000 })
    await page.goto(`${appUrl}/app/agents/${await currentAgentId(page)}/connection_configure`)
    await expect(page.getByTestId('connection-setup-surface')).toBeVisible({ timeout: 15000 })

    await activateConnection(page, {
      name: 'E2E Read API',
      baseUrl: fixtureDockerUrl,
      specUrl: `${fixtureDockerUrl}/openapi.json`,
      authType: 'none',
    })
    await expect(page.getByText('1/1 ready').first()).toBeVisible({ timeout: 30000 })

    await page.getByLabel('Enabled').check()
    await page.getByText('Access').locator('..').getByRole('combobox').selectOption('anonymous')
    await page.getByRole('button', { name: 'Save deployment' }).click()

    await screenshot(page, evidence, 'builder-activated')

    const publicContext = await browser.newContext({ viewport: { width: 1280, height: 900 } })
    const publicPage = await publicContext.newPage()
    await publicPage.goto(`${appUrl}/a/${slug}`)
    await publicPage.getByPlaceholder('Describe what you need done').fill('what products do you have?')
    await publicPage.keyboard.press('Enter')
    await expect(publicPage.getByText('Sandbox Hoodie')).toBeVisible({ timeout: 20000 })
    await assertNoPublicLeaks(publicPage)
    await screenshot(publicPage, evidence, 'public-storefront-read')

    await page.goto(`${appUrl}/app/agents/${await currentAgentId(page)}/connection_configure`)
    await expect(page.getByTestId('connection-setup-surface')).toBeVisible({ timeout: 15000 })
    await activateConnection(page, {
      name: 'E2E Write API',
      baseUrl: fixtureDockerUrl,
      specUrl: `${fixtureDockerUrl}/admin/openapi.json`,
      authType: 'bearer',
      credential: 'e2e-admin-token',
    })
    await expect(page.getByText('2/2 ready')).toBeVisible({ timeout: 30000 })

    await publicPage.goto(`${appUrl}/a/${slug}`)
    await publicPage.getByPlaceholder('Describe what you need done').fill('create product title=E2E-Hat')
    await publicPage.keyboard.press('Enter')
    await expect(publicPage.getByText(/needs approval/i)).toBeVisible({ timeout: 20000 })
    await assertNoPublicLeaks(publicPage)
    await expectAdminWrites(0)

    await expect(page.getByTestId('pending-approvals-card')).toBeVisible({ timeout: 20000 })
    await page.getByTestId('pending-approvals-card').getByRole('button', { name: 'Approve' }).first().click()
    await expect.poll(() => adminWriteCount(), { timeout: 20000 }).toBe(1)
    await expect(publicPage.getByText(/approved request ran successfully/i)).toBeVisible({ timeout: 20000 })
    await assertNoPublicLeaks(publicPage)
    await screenshot(page, evidence, 'builder-approval-approved')

    await publicPage.getByPlaceholder('Describe what you need done').fill('create product title=E2E-Cancel')
    await publicPage.keyboard.press('Enter')
    await expect(publicPage.getByText(/needs approval/i)).toBeVisible({ timeout: 20000 })
    await expect(page.getByTestId('pending-approvals-card')).toBeVisible({ timeout: 20000 })
    await page.getByTestId('pending-approvals-card').getByRole('button', { name: 'Cancel' }).first().click()
    await expect(publicPage.getByText(/owner canceled this request/i)).toBeVisible({ timeout: 20000 })
    await assertNoPublicLeaks(publicPage)
    await page.waitForTimeout(1500)
    await expectAdminWrites(1)

    await browser.close()
    console.log(JSON.stringify({ ok: true, evidence }, null, 2))
  } catch (error) {
    await screenshot(page, evidence, 'failure').catch(() => undefined)
    await browser.close()
    console.error(JSON.stringify({ ok: false, evidence, error: String(error) }, null, 2))
    process.exitCode = 1
  } finally {
    if (fixtureProcess) fixtureProcess.kill('SIGTERM')
  }
}

async function activateConnection(page, { name, baseUrl, specUrl, authType, credential = '' }) {
  const surface = page.getByTestId('connection-setup-surface')
  const form = surface.locator('form').last()
  await form.scrollIntoViewIfNeeded()
  await form.getByLabel('Connection name *').fill(name)
  await form.getByLabel('Base URL *').fill(baseUrl)
  await form.getByLabel('OpenAPI URL').fill(specUrl)
  await form.getByLabel('Auth type *').selectOption(authType)
  if (credential) {
    await form.getByLabel('Credential').fill(credential)
  }
  await form.getByRole('button', { name: 'Save and activate API' }).click()
  await expect(page.getByText(/activated|created|generated|Catalog/i).first()).toBeVisible({ timeout: 30000 })
}

async function currentAgentId(page) {
  const url = new URL(page.url())
  const match = url.pathname.match(/\/app\/agents\/([^/]+)/)
  if (!match) throw new Error(`Could not resolve agent id from ${url.pathname}`)
  return match[1]
}

async function assertNoPublicLeaks(page) {
  const text = (await page.locator('body').innerText()).toLowerCase()
  for (const leak of forbiddenPublicLeaks) {
    if (text.includes(leak)) {
      throw new Error(`Public deployed chat leaked internal text: ${leak}`)
    }
  }
}

async function screenshot(page, evidence, name) {
  const file = path.join(artifactRoot, `${name}.png`)
  await page.screenshot({ path: file, fullPage: true })
  evidence.screenshots.push(file)
}

async function ensureFixture() {
  const healthy = await fetchJson(`${fixtureLocalUrl}/__fixture/admin-writes`).then(() => true).catch(() => false)
  if (healthy) return

  fixtureProcess = spawn(process.execPath, [path.join(__dirname, 'mock-storefront-api.mjs')], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, MOCK_STOREFRONT_PORT: '9109' },
  })
  fixtureProcess.stdout.on('data', (chunk) => process.stdout.write(chunk))
  fixtureProcess.stderr.on('data', (chunk) => process.stderr.write(chunk))
  await expect.poll(
    async () => fetchJson(`${fixtureLocalUrl}/__fixture/admin-writes`).then(() => true).catch(() => false),
    { timeout: 5000 },
  ).toBe(true)
}

async function requireOk(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${url} returned ${response.status}`)
}

async function fetchJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${url} returned ${response.status}`)
  return response.json()
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`${url} returned ${response.status}`)
  return response.json()
}

async function adminWriteCount() {
  const body = await fetchJson(`${fixtureLocalUrl}/__fixture/admin-writes`)
  return Number(body.count || 0)
}

async function expectAdminWrites(expected) {
  const actual = await adminWriteCount()
  if (actual !== expected) {
    throw new Error(`Expected ${expected} admin fixture writes, got ${actual}`)
  }
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
