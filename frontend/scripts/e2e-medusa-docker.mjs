import fs from 'node:fs/promises'
import http from 'node:http'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { chromium, expect } from '@playwright/test'

const appUrl = process.env.E2E_APP_URL || 'http://localhost:3007'
const medusaBackendUrl = process.env.E2E_MEDUSA_BACKEND_URL || 'http://host.docker.internal:9000'
const medusaSchemaPath =
  process.env.E2E_MEDUSA_STORE_SCHEMA_PATH ||
  path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    '..',
    '..',
    'integration_prep',
    'openapi_toolrouter',
    'vendor',
    'openapi_toolrouter_benchmark',
    'artifacts',
    'raw_openapi',
    'medusa_store.yaml',
  )
const medusaHeaderName = process.env.E2E_MEDUSA_PUBLISHABLE_KEY_HEADER || 'x-publishable-api-key'
const schemaPort = Number(process.env.E2E_MEDUSA_SCHEMA_PORT || 9110)
const medusaSchemaLocalUrl = `http://localhost:${schemaPort}/medusa-store.yaml`
const medusaSchemaDockerUrl = `http://host.docker.internal:${schemaPort}/medusa-store.yaml`
const datasetQuery = process.env.E2E_MEDUSA_QUERY || 'list products'
const artifactRoot =
  process.env.SAASTOAGENT_E2E_ARTIFACT_DIR ||
  path.join(os.tmpdir(), `saastoagent-medusa-ui-e2e-${Date.now()}`)

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const workspaceRoot = path.resolve(__dirname, '..', '..', '..', '..')
const medusaCredsPath =
  process.env.E2E_MEDUSA_CREDS_PATH || path.join(workspaceRoot, 'test_targets', 'CREDS.md')

const forbiddenPublicLeaks = [
  'getproducts',
  'postproducts',
  'listproducts',
  '/store/products',
  '/admin/products',
  'operationid',
  'score',
  'trace',
  'trace id',
  'tool_start',
  'tool_end',
  'tool event',
  'approval id',
]

async function main() {
  await fs.mkdir(artifactRoot, { recursive: true })
  const publishableKey = await readPublishableKey()
  const medusaRawSchema = await fs.readFile(medusaSchemaPath, 'utf8')
  const schemaServer = await startSchemaServer(medusaRawSchema)
  const runId = Date.now()
  const email = `medusa-ui-e2e-${runId}@example.com`
  const password = 'SaaStoAgent123!'
  const slug = `live-medusa-${runId}`
  const evidence = {
    artifactRoot,
    appUrl,
    medusaBackendUrl,
    medusaSchemaPath,
    medusaSchemaLocalUrl,
    medusaSchemaDockerUrl,
    medusaHeaderName,
    query: datasetQuery,
    ownerCredentials: { email, password },
    slug,
    deployedUrl: `${appUrl}/a/${slug}`,
    screenshots: [],
  }

  const browser = await chromium.launch({ headless: process.env.E2E_HEADLESS !== '0' })
  const owner = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await owner.newPage()

  try {
    await gotoWithRetry(page, `${appUrl}/register`)
    await page.getByTestId('corpus-auth-display-name').fill('Medusa UI E2E Owner')
    await page.getByTestId('corpus-auth-email').fill(email)
    await page.getByTestId('corpus-auth-password').fill(password)
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page.getByTestId('auth-user-pill')).toContainText(email, { timeout: 20000 })

    await page.getByRole('button', { name: /Create SaaS Agent/ }).first().click()
    const createAgentSurface = page.getByTestId('corpus-operation-review-surface')
    await expect(createAgentSurface).toBeVisible({ timeout: 15000 })
    await createAgentSurface.locator('[data-qa-field="name"]').fill(`Live Commerce ${runId}`)
    await createAgentSurface.locator('[data-qa-field="slug"]').fill(slug)
    await createAgentSurface.getByRole('button', { name: /Continue|Create SaaS Agent/ }).click()
    await expect(page).toHaveURL(/\/app\/agents\//, { timeout: 20000 })

    await openConnectionSetupFromRail(page)

    await activateConnection(page, {
      name: 'Live Commerce Store API',
      baseUrl: medusaBackendUrl,
      specUrl: medusaSchemaDockerUrl,
      credential: publishableKey,
      headerName: medusaHeaderName,
    })
    await expect(page.getByText('1/1 ready').first()).toBeVisible({ timeout: 120000 })

    await page.getByLabel('Enabled').check()
    await page.getByText('Access').locator('..').getByRole('combobox').selectOption('anonymous')
    await page.getByRole('complementary').getByRole('button', { name: 'Save deployment' }).click()
    await commitDeploymentReview(page)
    await screenshot(page, evidence, 'builder-medusa-activated')

    const publicContext = await browser.newContext({ viewport: { width: 1280, height: 900 } })
    const publicPage = await publicContext.newPage()
    await gotoWithRetry(publicPage, evidence.deployedUrl)
    await sendPublicMessage(publicPage, datasetQuery, /Medusa T-Shirt|Medusa Sweatshirt|Medusa Sweatpants|Medusa Shorts/i)
    await assertNoPublicLeaks(publicPage)
    await screenshot(publicPage, evidence, 'public-medusa-products')

    const searchBubble = await sendPublicMessage(publicPage, 'search for sweatshirt', /Medusa Sweatshirt/i)
    await expect(searchBubble).not.toContainText('Medusa T-Shirt')
    await screenshot(publicPage, evidence, 'public-medusa-search-sweatshirt')

    const filterBubble = await sendPublicMessage(publicPage, 'filter for shorts', /Medusa Shorts/i)
    await expect(filterBubble).not.toContainText('Medusa Sweatshirt')
    await screenshot(publicPage, evidence, 'public-medusa-filter-shorts')

    const productSwitchBubble = await sendPublicMessage(publicPage, 'i want to buy Medusa T-Shirt', /Medusa T-Shirt/i)
    await expect(productSwitchBubble).not.toContainText('Medusa Sweatshirt')
    await screenshot(publicPage, evidence, 'public-medusa-product-switch')

    await sendPublicMessage(publicPage, 'add the L size to cart', /owner-approved automation policy/i)
    await assertNoPublicLeaks(publicPage)
    await screenshot(publicPage, evidence, 'public-medusa-add-cart-policy-needed')
    await approveLatestPolicyCandidate(page, evidence, 'add-cart')

    await sendPublicMessage(publicPage, 'add the L size to cart', /Done\. I handled that for you\./i)
    await assertNoPublicLeaks(publicPage)
    await screenshot(publicPage, evidence, 'public-medusa-add-cart-done')

    const checkoutResult = await runCheckoutLoop({
      ownerPage: page,
      publicPage,
      evidence,
      maxAttempts: 10,
    })
    evidence.checkout = checkoutResult
    await screenshot(publicPage, evidence, checkoutResult.completed ? 'public-medusa-checkout-done' : 'public-medusa-checkout-blocked')

    if (!checkoutResult.completed) {
      throw new Error(`Checkout did not complete in the public flow: ${checkoutResult.reason}`)
    }

    await browser.close()
    console.log(JSON.stringify({ ok: true, evidence }, null, 2))
  } catch (error) {
    await screenshot(page, evidence, 'failure').catch(() => undefined)
    await browser.close()
    console.error(JSON.stringify({ ok: false, evidence, error: String(error) }, null, 2))
    process.exitCode = 1
  } finally {
    await new Promise((resolve) => schemaServer.close(resolve))
  }
}

async function gotoWithRetry(page, url) {
  let lastError
  for (let attempt = 0; attempt < 12; attempt += 1) {
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 })
      return
    } catch (error) {
      lastError = error
      await page.waitForTimeout(2500)
    }
  }
  throw lastError
}

async function activateConnection(page, { name, baseUrl, specUrl, credential, headerName }) {
  const surface = page.getByTestId('connection-setup-surface')
  const form = surface.locator('form').nth(1)
  await form.getByLabel('Connection name *').fill(name)
  await form.getByLabel('Base URL *').fill(baseUrl)
  await form.getByLabel('OpenAPI URL').fill(specUrl)
  await form.getByLabel('Auth type *').selectOption('api_key_header')
  await form.getByLabel('Credential', { exact: true }).fill(credential)
  await form.getByLabel('Header name', { exact: true }).fill(headerName)
  await form.getByRole('button', { name: 'Save and activate API' }).click()
  await expect(page.getByText(/activated|created|generated|Catalog/i).first()).toBeVisible({ timeout: 60000 })
}

async function openConnectionSetupFromRail(page) {
  const rail = page.getByTestId('capability-rail')
  await expect(rail).toBeVisible({ timeout: 20000 })
  await rail.getByRole('button', { name: 'Connect API' }).click()
  await expect(page.getByTestId('connection-setup-surface')).toBeVisible({ timeout: 20000 })
}

async function commitDeploymentReview(page) {
  const surface = page.getByTestId('corpus-operation-review-surface')
  await expect(surface).toBeVisible({ timeout: 15000 })
  await surface.getByRole('button', { name: 'Save deployment' }).click()
  await expect(page.getByText(/Deployment settings saved/i).first()).toBeVisible({ timeout: 15000 })
}

async function sendPublicMessage(page, message, expected, timeout = 90000) {
  const input = page.getByPlaceholder('Describe what you need done')
  await expect(input).toBeEnabled({ timeout })
  const assistantMessages = page.locator('[data-testid="message-bubble"][data-message-role="assistant"]')
  const before = await assistantMessages.count()
  await input.fill(message)
  await input.press('Enter')
  const bubble = assistantMessages.nth(before)
  await expect(bubble).toContainText(expected, { timeout })
  await assertNoPublicLeaks(page)
  await expect(input).toBeEnabled({ timeout: 30000 })
  return bubble
}

async function approveLatestPolicyCandidate(page, evidence, label) {
  await page.bringToFront()
  const rail = page.getByTestId('capability-rail')
  await rail.getByRole('button', { name: /Learning/i }).click()
  await expect(page.getByRole('heading', { name: /Sandbox learning|Learning review/i })).toBeVisible({ timeout: 20000 })

  if (await page.getByRole('heading', { name: 'Learning review' }).isVisible().catch(() => false)) {
    await page.getByTitle('Approve learning').click()
    await expect(page.getByRole('heading', { name: 'Sandbox learning' })).toBeVisible({ timeout: 20000 })
    await screenshot(page, evidence, `owner-learning-${label}-approved`)
    return
  }

  await page.getByRole('button', { name: 'Policy gaps' }).click()
  const candidate = page
    .locator('li')
    .filter({ hasText: 'domain_policy_gap' })
    .filter({ hasText: 'proposed' })
    .first()
  await expect(candidate).toBeVisible({ timeout: 30000 })
  await screenshot(page, evidence, `owner-learning-${label}-candidate`)
  await candidate.getByTitle('Open review').click()
  await expect(page.getByRole('heading', { name: 'Learning review' })).toBeVisible({ timeout: 20000 })
  await screenshot(page, evidence, `owner-learning-${label}-review`)
  await page.getByTitle('Approve learning').click()
  await expect(page.getByRole('heading', { name: 'Sandbox learning' })).toBeVisible({ timeout: 20000 })
  await screenshot(page, evidence, `owner-learning-${label}-approved`)
}

async function runCheckoutLoop({ ownerPage, publicPage, evidence, maxAttempts }) {
  let intent = 'checkout'
  const turns = []
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const bubble = await sendPublicMessage(
      publicPage,
      intent,
      /owner-approved automation policy|Done\. I handled that for you\.|I found multiple options|I need one more detail|connected API returned an error|could not complete/i,
      120000,
    )
    const text = await bubble.innerText()
    turns.push({ attempt, intent, response: text })
    await screenshot(publicPage, evidence, `public-medusa-checkout-attempt-${attempt}`)

    if (/owner-approved automation policy/i.test(text)) {
      await approveLatestPolicyCandidate(ownerPage, evidence, `checkout-${attempt}`)
      continue
    }

    if (/I found multiple options/i.test(text)) {
      const option = firstBulletLabel(text)
      if (!option) {
        return { completed: false, reason: 'choice prompt did not expose a selectable label', turns }
      }
      intent = `use ${option}`
      continue
    }

    if (/Done\. I handled that for you\./i.test(text)) {
      if (intent === 'checkout') {
        return { completed: true, reason: 'checkout completed', turns }
      }
      intent = 'checkout'
      continue
    }

    return { completed: false, reason: text.replace(/\s+/g, ' ').slice(0, 240), turns }
  }
  return { completed: false, reason: `checkout did not complete within ${maxAttempts} turns`, turns }
}

function firstBulletLabel(text) {
  const bullet = text.match(/^\s*(?:[-*]|\d+[.)])\s+(.+)$/m)
  if (bullet) return bullet[1].trim()
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !/^\d{1,2}:\d{2}/.test(line))
  const promptIndex = lines.findIndex((line) => /which one should i use/i.test(line))
  const options = lines
    .slice(promptIndex >= 0 ? promptIndex + 1 : 0)
    .filter((line) => !/[?.]$/.test(line))
    .filter((line) => line.length <= 80)
  return options[0] || null
}

async function startSchemaServer(rawSchema) {
  const server = http.createServer((request, response) => {
    if (request.url !== '/medusa-store.yaml') {
      response.writeHead(404, { 'content-type': 'text/plain' })
      response.end('not found')
      return
    }
    response.writeHead(200, { 'content-type': 'application/yaml' })
    response.end(rawSchema)
  })
  await new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(schemaPort, '0.0.0.0', resolve)
  })
  return server
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

async function readPublishableKey() {
  const raw = await fs.readFile(medusaCredsPath, 'utf8')
  const match = raw.match(/Publishable API key:\s*([^\s]+)/i)
  if (!match) {
    throw new Error(`Could not read publishable API key from ${medusaCredsPath}`)
  }
  return match[1]
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
