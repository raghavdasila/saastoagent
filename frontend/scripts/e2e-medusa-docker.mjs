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

    await page.getByRole('button', { name: /Create Agent/ }).first().click()
    const createAgentProposal = page.getByTestId('corpus-proposal-surface')
    await expect(createAgentProposal).toBeVisible({ timeout: 15000 })
    await createAgentProposal.locator('input').nth(0).fill(`Live Commerce ${runId}`)
    await createAgentProposal.locator('input').nth(1).fill(slug)
    await createAgentProposal.getByRole('button', { name: /Continue|Create SaaS Agent/ }).click()
    await expect(page).toHaveURL(/\/app\/agents\//, { timeout: 20000 })

    await page.getByPlaceholder('Message Corpus').fill('set up the API connection')
    await page.keyboard.press('Enter')
    await expect(page.getByTestId('connection-setup-surface')).toBeVisible({ timeout: 20000 })

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
    await page.getByRole('button', { name: 'Save deployment' }).click()
    await screenshot(page, evidence, 'builder-medusa-activated')

    const publicContext = await browser.newContext({ viewport: { width: 1280, height: 900 } })
    const publicPage = await publicContext.newPage()
    await gotoWithRetry(publicPage, evidence.deployedUrl)
    await publicPage.getByPlaceholder('Describe what you need done').fill(datasetQuery)
    await publicPage.keyboard.press('Enter')
    await expect(publicPage.getByText(/Medusa T-Shirt|Medusa Sweatshirt|Medusa Sweatpants|Medusa Shorts/i)).toBeVisible({
      timeout: 60000,
    })
    await assertNoPublicLeaks(publicPage)
    await screenshot(publicPage, evidence, 'public-medusa-products')

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
