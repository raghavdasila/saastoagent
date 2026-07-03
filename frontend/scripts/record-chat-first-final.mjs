import fs from 'node:fs/promises'
import path from 'node:path'

import { chromium, expect } from '@playwright/test'

const browserAppUrl = process.env.DEMO_BROWSER_APP_URL || process.env.DEMO_APP_URL || 'http://localhost:3000'
const apiAppUrl = process.env.DEMO_API_APP_URL || process.env.DEMO_APP_URL || browserAppUrl
const stamp = process.env.DEMO_STAMP || String(Date.now())
const medusaPublishableKey = process.env.DEMO_MEDUSA_PUBLISHABLE_KEY || ''
const artifactRoot = process.env.DEMO_ARTIFACT_DIR || `/tmp/chat-first-final-${stamp}`
const chromiumExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium-browser'
const cdpEndpoint = process.env.DEMO_CDP_ENDPOINT || ''
const externalVideoPath = process.env.DEMO_EXTERNAL_VIDEO_PATH || ''
const checkpointMode = process.env.DEMO_CHECKPOINT || 'full'
const checkpointInputPath = process.env.DEMO_CHECKPOINT_INPUT || ''
const checkpointOutputPath = process.env.DEMO_CHECKPOINT_OUTPUT || path.join(artifactRoot, 'checkpoint.json')
const recordVideo = process.env.DEMO_RECORD_VIDEO !== '0'
const pauseScale = Number(process.env.DEMO_PAUSE_SCALE || '1')
const viewportWidth = numberFromEnv('DEMO_VIEWPORT_WIDTH', 1440)
const viewportHeight = numberFromEnv('DEMO_VIEWPORT_HEIGHT', 900)
const corpusTypingDelayMs = numberFromEnv('DEMO_CORPUS_TYPE_DELAY_MS', 32)
const publicTypingDelayMs = numberFromEnv('DEMO_PUBLIC_TYPE_DELAY_MS', 28)
const fieldTypingDelayMs = numberFromEnv('DEMO_FIELD_TYPE_DELAY_MS', 18)
const formTypingDelayMs = numberFromEnv('DEMO_FORM_TYPE_DELAY_MS', 22)
const videoDir = path.join(artifactRoot, 'videos')
const screenshotDir = path.join(artifactRoot, 'screenshots')

const ownerEmail = `corpus-video-${stamp}@example.com`
const ownerPassword = 'SaaStoAgent123!'
const ownerDisplayName = `Corpus Video ${stamp}`
const agentName = `Medusa Shopping Assistant ${stamp.slice(-4)}`
const agentSlug = `medusa-shopping-assistant-${stamp.slice(-4)}`
let ownerToken = null

const externalPolicySeeds = [
  {
    title: 'Approved visitor cart item policy',
    target_action_path: '/store/carts/{id}/line-items',
    target_risk_level: 'write',
    allowed_action_paths: ['/store/carts', '/store/carts/{id}/line-items'],
  },
  {
    title: 'Approved visitor shipping policy',
    target_action_path: '/store/carts/{id}/shipping-methods',
    target_risk_level: 'write',
    allowed_action_paths: ['/store/shipping-options', '/store/carts/{id}/shipping-methods'],
  },
  {
    title: 'Approved visitor payment collection policy',
    target_action_path: '/store/payment-collections',
    target_risk_level: 'financial',
    allowed_action_paths: ['/store/payment-collections'],
  },
  {
    title: 'Approved visitor payment session policy',
    target_action_path: '/store/payment-collections/{id}/payment-sessions',
    target_risk_level: 'financial',
    allowed_action_paths: ['/store/payment-collections', '/store/payment-collections/{id}/payment-sessions'],
  },
  {
    title: 'Approved visitor cart completion policy',
    target_action_path: '/store/carts/{id}/complete',
    target_risk_level: 'write',
    allowed_action_paths: ['/store/carts/{id}/complete'],
  },
  {
    title: 'Approved visitor cart update policy',
    target_action_path: '/store/carts/{id}',
    target_risk_level: 'write',
    allowed_action_paths: ['/store/carts/{id}'],
  },
]

if (!medusaPublishableKey) {
  throw new Error('Set DEMO_MEDUSA_PUBLISHABLE_KEY.')
}

async function main() {
  await fs.mkdir(videoDir, { recursive: true })
  await fs.mkdir(screenshotDir, { recursive: true })

  const browser = cdpEndpoint
    ? await chromium.connectOverCDP(cdpEndpoint)
    : await chromium.launch({
        headless: true,
        executablePath: chromiumExecutable,
        args: ['--no-sandbox', '--disable-dev-shm-usage'],
      })
  const context = cdpEndpoint
    ? browser.contexts()[0] || await browser.newContext()
    : await browser.newContext({
        viewport: { width: viewportWidth, height: viewportHeight },
        recordVideo: recordVideo ? {
          dir: videoDir,
          size: { width: viewportWidth, height: viewportHeight },
        } : undefined,
      })
  const page = cdpEndpoint ? context.pages()[0] || await context.newPage() : await context.newPage()
  await page.setViewportSize({ width: viewportWidth, height: viewportHeight }).catch(() => undefined)
  const evidence = {
    artifactRoot,
    appUrl: browserAppUrl,
    browserAppUrl,
    apiAppUrl,
    ownerEmail,
    ownerDisplayName,
    agentName,
    agentSlug,
    recordVideo,
    checkpointMode,
    pacing: {
      pauseScale,
      corpusTypingDelayMs,
      publicTypingDelayMs,
      fieldTypingDelayMs,
      formTypingDelayMs,
      viewportWidth,
      viewportHeight,
    },
    medusaKey: {
      prefix: medusaPublishableKey.slice(0, 10),
      length: medusaPublishableKey.length,
    },
    screenshots: [],
    ownerTurns: [],
    publicBoundaryTurns: [],
    policySeedRequest: null,
    policySeedResult: null,
    finalPublicTurns: [],
    ownerApprovals: [],
    phases: [],
  }

  try {
    if (checkpointMode === 'owner-setup') {
      await runPhase(evidence, 'owner_setup', () => recordOwnerSetup(page, evidence))
      await writeCheckpoint(evidence)
    } else if (checkpointMode === 'public-checkout') {
      await loadCheckpoint(evidence)
      await runPhase(evidence, 'seed_public_checkout_policies', () => waitForExternalPolicySeed(evidence))
      await runPhase(evidence, 'public_checkout', () => recordFinalPublicCheckout(page, evidence))
    } else if (checkpointMode === 'final-recording') {
      await runPhase(evidence, 'owner_setup', () => recordOwnerSetup(page, evidence))
      await runPhase(evidence, 'seed_checkout_policies', () => waitForExternalPolicySeed(evidence))
      await runPhase(evidence, 'chat_driven_policy_review', () => recordChatDrivenPolicyReview(page, evidence))
      await runPhase(evidence, 'public_checkout', () => recordFinalPublicCheckout(page, evidence))
    } else if (checkpointMode === 'full') {
      await runPhase(evidence, 'owner_setup', () => recordOwnerSetup(page, evidence))
      await runPhase(evidence, 'public_policy_boundary', () => recordVisiblePublicPolicyBoundary(page, evidence))
      await runPhase(evidence, 'owner_learning_approval', () => recordOwnerLearningApproval(page, evidence))
      await runPhase(evidence, 'seed_remaining_policies', () => waitForExternalPolicySeed(evidence))
      await runPhase(evidence, 'active_policies', () => recordActivePolicies(page, evidence))
      await runPhase(evidence, 'public_checkout', () => recordFinalPublicCheckout(page, evidence))
    } else {
      throw new Error(`Unknown DEMO_CHECKPOINT value: ${checkpointMode}`)
    }

    await pause(page, 4500)
    await closeBrowserSession({ browser, context, page })

    if (recordVideo) {
      const videos = await fs.readdir(videoDir)
      evidence.videos = videos.map((name) => path.join(videoDir, name))
    } else if (externalVideoPath) {
      evidence.videos = [externalVideoPath]
    } else {
      evidence.videos = []
    }
    await fs.writeFile(path.join(artifactRoot, 'recording-evidence.json'), JSON.stringify(evidence, null, 2))
    console.log(JSON.stringify({ ok: true, evidence }, null, 2))
  } catch (error) {
    await page.screenshot({ path: path.join(screenshotDir, 'failure.png'), fullPage: true }).catch(() => undefined)
    evidence.error = String(error?.stack || error)
    await closeBrowserSession({ browser, context, page }).catch(() => undefined)
    await fs.writeFile(path.join(artifactRoot, 'recording-evidence.json'), JSON.stringify(evidence, null, 2))
    console.error(JSON.stringify({ ok: false, evidence }, null, 2))
    process.exitCode = 1
  }
}

async function runPhase(evidence, name, fn) {
  const phase = {
    name,
    status: 'running',
    startedAt: new Date().toISOString(),
    durationMs: null,
  }
  evidence.phases.push(phase)
  const started = Date.now()
  console.log(JSON.stringify({ type: 'phase_start', name, startedAt: phase.startedAt }))
  try {
    const result = await fn()
    phase.status = 'passed'
    phase.finishedAt = new Date().toISOString()
    phase.durationMs = Date.now() - started
    console.log(JSON.stringify({ type: 'phase_pass', name, durationMs: phase.durationMs }))
    return result
  } catch (error) {
    phase.status = 'failed'
    phase.finishedAt = new Date().toISOString()
    phase.durationMs = Date.now() - started
    phase.error = String(error?.message || error)
    console.log(JSON.stringify({ type: 'phase_fail', name, durationMs: phase.durationMs, error: phase.error }))
    throw error
  }
}

async function writeCheckpoint(evidence) {
  const checkpoint = {
    stamp,
    createdAt: new Date().toISOString(),
    agentId: evidence.agentId,
    agentSlug: evidence.agentSlug,
    agentName: evidence.agentName,
    publicUrl: evidence.publicUrl,
    ownerEmail: evidence.ownerEmail,
    ownerDisplayName: evidence.ownerDisplayName,
  }
  if (!checkpoint.agentId || !checkpoint.publicUrl) {
    throw new Error('Cannot write checkpoint before agentId and publicUrl are available.')
  }
  await fs.writeFile(checkpointOutputPath, JSON.stringify(checkpoint, null, 2))
  evidence.checkpointOutput = checkpointOutputPath
  console.log(JSON.stringify({ type: 'checkpoint_written', path: checkpointOutputPath, agentId: checkpoint.agentId }))
}

async function loadCheckpoint(evidence) {
  if (!checkpointInputPath) {
    throw new Error('Set DEMO_CHECKPOINT_INPUT for DEMO_CHECKPOINT=public-checkout.')
  }
  const checkpoint = JSON.parse(await fs.readFile(checkpointInputPath, 'utf8'))
  if (!checkpoint.agentId || !checkpoint.publicUrl) {
    throw new Error(`Checkpoint is missing agentId/publicUrl: ${checkpointInputPath}`)
  }
  evidence.checkpointInput = checkpointInputPath
  evidence.agentId = checkpoint.agentId
  evidence.agentSlug = checkpoint.agentSlug
  evidence.agentName = checkpoint.agentName || evidence.agentName
  evidence.publicUrl = checkpoint.publicUrl
  evidence.ownerEmail = checkpoint.ownerEmail || evidence.ownerEmail
  evidence.ownerDisplayName = checkpoint.ownerDisplayName || evidence.ownerDisplayName
  console.log(JSON.stringify({ type: 'checkpoint_loaded', path: checkpointInputPath, agentId: evidence.agentId }))
}

async function recordOwnerSetup(page, evidence) {
  await page.goto(`${browserAppUrl}/app/home`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.evaluate(() => window.localStorage.clear())
  await page.reload({ waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('textbox', { name: 'Message Corpus' })).toBeVisible({ timeout: 30000 })
  await pause(page, 1200)
  await screenshot(page, evidence, '01-fresh-logged-out-corpus.png')

  evidence.ownerTurns.push(await sendCorpus(page, 'Hi Corpus. What are you, and what can you help me build today?', 'Corpus'))
  await screenshot(page, evidence, '02-corpus-intro-chat.png')

  evidence.ownerTurns.push(
    await sendCorpus(
      page,
      'I want to build a shopping assistant for my Medusa store. Can you help me sign up and get set up?',
      null,
      { waitForInput: false },
    ),
  )
  await expect(page.getByTestId('corpus-auth-surface')).toBeVisible({ timeout: 30000 })
  await screenshot(page, evidence, '03-chat-starts-signup-surface.png')

  const authSurface = page.getByTestId('corpus-auth-surface')
  await humanFill(authSurface.getByTestId('corpus-auth-display-name'), ownerDisplayName)
  await humanFill(authSurface.getByTestId('corpus-auth-email'), ownerEmail)
  await humanFill(authSurface.getByTestId('corpus-auth-password'), ownerPassword)
  await pause(page, 900)
  await authSurface.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByTestId('auth-user-pill')).toContainText(ownerEmail, { timeout: 60000 })
  await waitForCorpusSettled(page)
  ownerToken = await page.evaluate(() => window.localStorage.getItem('sta_v01_token'))
  if (!ownerToken) throw new Error('No owner token in localStorage after signup.')
  await screenshot(page, evidence, '04-signup-complete-chat-ready.png')

  evidence.ownerTurns.push(
    await sendCorpus(page, "Let's make the shopping assistant."),
  )
  await expect(page.getByTestId('corpus-operation-review-surface')).toBeVisible({ timeout: 30000 })
  await screenshot(page, evidence, '05-chat-opens-create-agent-review.png')

  const createReview = page.getByTestId('corpus-operation-review-surface')
  await fillOperationField(createReview, 'name', agentName)
  await fillOperationField(createReview, 'slug', agentSlug)
  await pause(page, 900)
  await createReview.getByRole('button', { name: 'Create SaaS Agent' }).click()
  await page.waitForURL(/\/app\/agents\/[^/]+/, { timeout: 60000 })
  evidence.agentId = parseAgentId(page.url())
  if (!evidence.agentId) throw new Error(`Could not parse agent id from ${page.url()}`)
  await expect(page.getByText(agentName).first()).toBeVisible({ timeout: 60000 })
  await waitForCorpusSettled(page)
  await screenshot(page, evidence, '06-agent-created-chat-confirmation.png')

  evidence.ownerTurns.push(
    await sendCorpus(page, 'Connect the API for my local Medusa store.'),
  )
  await page.waitForURL(/\/connection_configure/, { timeout: 60000 })
  await expect(page.getByTestId('connection-setup-surface')).toBeVisible({ timeout: 30000 })
  await screenshot(page, evidence, '07-chat-opens-secure-connection-surface.png')

  const connectionSurface = page.getByTestId('connection-setup-surface')
  const activateForm = connectionSurface.locator('form').filter({
    has: page.getByRole('button', { name: 'Save and activate API' }),
  })
  await expect(activateForm).toHaveCount(1)
  await fillOperationField(activateForm, 'name', 'Local Medusa Store API')
  await fillOperationField(activateForm, 'base_url', 'http://host.docker.internal:9000')
  await fillOperationField(activateForm, 'spec_url', 'http://host.docker.internal:9110/medusa_store.yaml')
  await selectOperationField(activateForm, 'auth_type', 'api_key_header')
  await fillOperationField(activateForm, 'credential_value', medusaPublishableKey)
  await fillOperationField(activateForm, 'header_name', 'x-publishable-api-key')
  await screenshot(page, evidence, '08-connection-fields-filled-masked.png')
  await activateForm.getByRole('button', { name: 'Save and activate API' }).click()
  await expect(page.getByText('API readiness').first()).toBeVisible({ timeout: 180000 })
  await expect(page.getByText('1/1 ready').first()).toBeVisible({ timeout: 180000 })
  await waitForCorpusSettled(page)
  await screenshot(page, evidence, '09-api-activation-ready.png')

  evidence.ownerTurns.push(
    await sendCorpus(
      page,
      'Can we publish this for test shoppers safely?',
      null,
      { waitForSettled: false, waitForInput: false },
    ),
  )
  const deploymentCard = page.getByTestId('deployment-settings-card')
  await expect(deploymentCard).toHaveCount(1)
  await expect(deploymentCard).toBeVisible({ timeout: 30000 })
  await deploymentCard.scrollIntoViewIfNeeded()
  await pause(page, 500)
  await screenshot(page, evidence, '10-chat-opens-deployment-review.png')
  await setOperationCheckbox(deploymentCard, 'enabled', true)
  await selectOperationField(deploymentCard, 'visitor_auth_mode', 'anonymous')
  await selectOperationField(deploymentCard, 'execution_mode', 'sandbox')
  await selectOperationField(deploymentCard, 'default_write_policy', 'confirm')
  await fillOperationField(
    deploymentCard,
    'welcome_message',
    'Ask me to browse products, build a cart, select shipping, create payment, and place a test order.',
  )
  await pause(page, 900)
  await screenshot(page, evidence, '10b-deployment-policy-controls-filled.png')
  const deploymentSubmit = deploymentCard.locator('button.surface-solid-button').filter({ hasText: /^Save deployment$/ })
  await expect(deploymentSubmit).toHaveCount(1)
  await clickWithFallback(deploymentSubmit, 'deployment settings submit')
  await waitForCorpusSettled(page)
  await expect(deploymentSubmit).toBeVisible({ timeout: 60000 })
  await expect(deploymentCard.locator('[data-qa-field="visitor_auth_mode"]')).toHaveValue('anonymous')
  await expect(deploymentCard.locator('[data-qa-field="execution_mode"]')).toHaveValue('sandbox')
  await expect(deploymentCard.locator('[data-qa-field="default_write_policy"]')).toHaveValue('confirm')
  await waitForDeploymentLive(evidence)
  await screenshot(page, evidence, '11-deployment-saved-chat-confirmation.png')

  evidence.publicUrl = `${browserAppUrl}/a/${agentSlug}`
}

async function recordVisiblePublicPolicyBoundary(page, evidence) {
  await page.goto(browserAppUrl, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.evaluate(() => window.localStorage.clear())
  await page.goto(evidence.publicUrl, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await expect(page.getByPlaceholder('Describe what you need done')).toBeVisible({ timeout: 30000 })
  await pause(page, 1500)
  await screenshot(page, evidence, '13-public-agent-fresh-anonymous.png')

  evidence.publicBoundaryTurns.push(
    await sendPublicMessage(page, 'Hi, what can you help me with?', ['products', 'cart', 'checkout', 'shop']),
  )
  evidence.publicBoundaryTurns.push(
    await sendPublicMessage(page, 'What products do you have?', ['Medusa', 'Sweatshirt', 'products']),
  )
  evidence.publicBoundaryTurns.push(
    await sendPublicMessage(page, 'The sweatshirt sounds good. What sizes are available?', ['M', 'sizes', 'Sweatshirt']),
  )
  await naturalAddMediumSweatshirt(page, evidence.publicBoundaryTurns, {
    expectedFinal: 'owner-approved automation policy',
  })
  await screenshot(page, evidence, '14-public-policy-boundary-visible.png')
}

async function recordOwnerLearningApproval(page, evidence) {
  await page.goto(`${browserAppUrl}/app/home`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.evaluate(
    ({ token, agentId }) => {
      window.localStorage.setItem('sta_v01_token', token)
      window.localStorage.setItem('sta_v01_saas_agent_id', agentId)
    },
    { token: ownerToken, agentId: evidence.agentId },
  )
  await page.goto(`${browserAppUrl}/app/agents/${evidence.agentId}`, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await expect(page.getByTestId('auth-user-pill')).toContainText(ownerEmail, { timeout: 60000 })
  await waitForCorpusReady(page)
  await screenshot(page, evidence, '15-owner-back-from-public.png')

  evidence.ownerTurns.push(
    await sendCorpus(page, 'Show me the Sandbox Learning review queue for that shopper attempt.'),
  )
  await page.waitForURL(/\/learning/, { timeout: 60000 })
  await expect(page.getByText('Sandbox learning').first()).toBeVisible({ timeout: 60000 })
  await expect(page.getByRole('button', { name: 'Policy gaps' })).toBeVisible({ timeout: 60000 })
  await screenshot(page, evidence, '16-chat-opens-learning-policy-gap.png')

  const approvalsBefore = await apiGet(`/api/saas-agents/${evidence.agentId}/agent/learnings`, ownerToken)
  evidence.ownerApprovals.push({
    stage: 'before_visible_approval',
    proposed: approvalsBefore.filter((candidate) => candidate.status === 'proposed').length,
  })
  const approveButton = page.locator('button[title="Approve learning"]')
  await expect(approveButton.first()).toBeVisible({ timeout: 60000 })
  await approveButton.first().click()
  await pause(page, 2600)
  await screenshot(page, evidence, '17-learning-policy-approved-visible.png')
}

async function waitForExternalPolicySeed(evidence) {
  const requestPath = path.join(artifactRoot, 'seed-request.json')
  const donePath = path.join(artifactRoot, 'seed-done.json')
  const request = {
    agentId: evidence.agentId,
    agentSlug: evidence.agentSlug,
    ownerEmail: evidence.ownerEmail,
    policies: externalPolicySeeds,
  }
  await fs.writeFile(requestPath, JSON.stringify(request, null, 2))
  evidence.policySeedRequest = requestPath
  const started = Date.now()
  while (Date.now() - started < 240_000) {
    try {
      const doneBuffer = await fs.readFile(donePath)
      const doneRaw =
        doneBuffer[0] === 0xff && doneBuffer[1] === 0xfe || doneBuffer.includes(0)
          ? doneBuffer.toString('utf16le')
          : doneBuffer.toString('utf8')
      const normalized = doneRaw.replace(/^\uFEFF/, '').trim()
      if (!normalized) {
        await new Promise((resolve) => setTimeout(resolve, 500))
        continue
      }
      if (!normalized.startsWith('{') && !normalized.startsWith('[')) {
        throw new Error(`Policy seed helper wrote non-JSON output: ${normalized.slice(0, 240)}`)
      }
      try {
        const done = JSON.parse(normalized)
        evidence.policySeedResult = done
        return
      } catch {
        await new Promise((resolve) => setTimeout(resolve, 500))
        continue
      }
    } catch (error) {
      if (!['ENOENT', 'EACCES', 'EBUSY'].includes(error?.code)) throw error
      await new Promise((resolve) => setTimeout(resolve, 500))
    }
  }
  throw new Error(`Timed out waiting for seeded policy confirmation at ${donePath}`)
}

async function recordActivePolicies(page, evidence) {
  await page.goto(`${browserAppUrl}/app/agents/${evidence.agentId}/learning?surface_id=learning.policy_gaps`, {
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  })
  await expect(page.getByText('Sandbox learning').first()).toBeVisible({ timeout: 60000 })
  await page.getByRole('button', { name: 'Active policies' }).click()
  await expect(page.getByText('approved').first()).toBeVisible({ timeout: 60000 })
  await pause(page, 1600)
  await screenshot(page, evidence, '18-learning-active-policies-visible.png')
}

async function recordChatDrivenPolicyReview(page, evidence) {
  evidence.ownerTurns.push(
    await sendCorpus(
      page,
      'How will actions be guarded if a shopper tries to check out? Show me the active checkout policies so I can review them.',
      null,
      { waitForSettled: false, waitForInput: false },
    ),
  )
  await expect.poll(() => page.url(), { timeout: 60000 }).toContain('/learning')
  await expect(page.getByText('Sandbox learning').first()).toBeVisible({ timeout: 60000 })
  await expect(page.getByRole('button', { name: 'Policy gaps' })).toBeVisible({ timeout: 60000 })
  await screenshot(page, evidence, '12-chat-opens-policy-review.png')

  await page.getByRole('button', { name: 'Active policies' }).click()
  await expect(page.getByText('approved').first()).toBeVisible({ timeout: 60000 })
  await pause(page, 1600)
  await screenshot(page, evidence, '18-chat-reviewed-active-policies.png')
}

async function recordFinalPublicCheckout(page, evidence) {
  await page.goto(browserAppUrl, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.evaluate(() => window.localStorage.clear())
  await page.goto(evidence.publicUrl, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await expect(page.getByPlaceholder('Describe what you need done')).toBeVisible({ timeout: 30000 })
  await pause(page, 1400)
  await screenshot(page, evidence, '19-public-final-fresh-session.png')

  evidence.finalPublicTurns.push(
    await sendPublicMessage(page, 'Hi, what products do you have?', ['Medusa', 'Sweatshirt', 'products']),
  )
  evidence.finalPublicTurns.push(
    await sendPublicMessage(page, 'The sweatshirt sounds good. What sizes are available?', ['M', 'sizes', 'Sweatshirt']),
  )
  await naturalAddMediumSweatshirt(page, evidence.finalPublicTurns, { expectedFinal: 'Done' })
  evidence.finalPublicTurns.push(
    await sendPublicMessage(page, 'What shipping options do I have?', ['Standard Shipping', 'shipping']),
  )
  evidence.finalPublicTurns.push(await sendPublicMessage(page, 'Standard Shipping works.', ['Done', 'Standard']))
  await continueNaturalPayment(page, evidence.finalPublicTurns)
  evidence.finalPublicTurns.push(await sendPublicMessage(page, 'Place the order.', 'order_'))

  const pageText = await page.locator('body').innerText()
  const orderMatch = pageText.match(/order_[A-Z0-9_]+/)
  if (!orderMatch) throw new Error('Checkout completed but no order id was visible.')
  const orderId = orderMatch[0].replace(/[).,;:!?]+$/, '')
  const lookup = 'Can you show my order?'
  const orderReadback = await sendPublicMessage(page, lookup, ['Order #', orderId])
  evidence.orderId = orderId
  evidence.finalPublicTurns.push(orderReadback)
  await screenshot(page, evidence, '20-public-final-order-readback.png')
}

async function naturalAddMediumSweatshirt(page, turns, { expectedFinal }) {
  let response = await sendPublicMessage(page, "I'll take a medium.", [
    expectedFinal,
    'add it to your cart',
    'add this to your cart',
    'add one to your cart',
    'add this',
    'add it',
    'which product',
    'country',
    'region',
    'shipping',
  ])
  turns.push(response)
  let text = response.assistant.toLowerCase()
  if (text.includes('which product') || text.includes('what product') || text.includes('which item')) {
    response = await sendPublicMessage(page, 'The sweatshirt, please.', [expectedFinal, 'country', 'region'])
    turns.push(response)
    text = response.assistant.toLowerCase()
  }
  if (
    text.includes('add it to your cart') ||
    text.includes('add this to your cart') ||
    text.includes('add one to your cart') ||
    text.includes('add this') ||
    text.includes('add it') ||
    text.includes('would you like me to add')
  ) {
    response = await sendPublicMessage(page, 'Yes, please add it to my cart.', [
      expectedFinal,
      'country',
      'region',
      'shipping',
    ])
    turns.push(response)
    text = response.assistant.toLowerCase()
  }
  if (text.includes('country') || text.includes('region')) {
    response = await sendPublicMessage(page, 'Denmark.', expectedFinal)
    turns.push(response)
  }
}

async function continueNaturalPayment(page, turns) {
  let response = await sendPublicMessage(page, 'How can I pay?', [
    'pp_system_default',
    'payment provider',
    'payment collection',
    'created',
    'Done',
  ])
  turns.push(response)
  let text = response.assistant.toLowerCase()
  if (text.includes('payment collection') && !text.includes('pp_system_default')) {
    response = await sendPublicMessage(page, 'Please continue to payment.', ['Done', 'pp_system_default'])
    turns.push(response)
    text = response.assistant.toLowerCase()
  }
  if (!text.includes('pp_system_default')) {
    response = await sendPublicMessage(page, 'What payment options can I use?', ['pp_system_default'])
    turns.push(response)
    text = response.assistant.toLowerCase()
  }
  response = await sendPublicMessage(page, 'Use the default payment option.', ['Done', 'payment session', 'pp_system_default'])
  turns.push(response)
  text = response.assistant.toLowerCase()
  if (!text.includes('done') && !text.includes('payment session')) {
    response = await sendPublicMessage(page, 'Use pp_system_default.', ['Done', 'payment session'])
    turns.push(response)
  }
}

async function sendCorpus(page, message, expectedText = null, options = {}) {
  const input = page.getByTestId('corpus-command-input')
  const sendButton = page.getByTestId('corpus-command-send')
  await expect(input).toBeEnabled({ timeout: 60000 })
  const assistantMessages = page.locator('[data-testid="message-bubble"][data-message-role="assistant"]')
  const before = await assistantMessages.count()
  await input.fill('')
  await input.type(message, { delay: corpusTypingDelayMs })
  await pause(page, 650)
  await sendButton.click()
  const bubble = assistantMessages.nth(before)
  await expect(bubble).toBeVisible({ timeout: 120000 })
  if (expectedText) {
    await expect(bubble).toContainText(expectedText, { timeout: 120000 })
  }
  if (options.waitForSettled !== false) {
    await waitForCorpusSettled(page)
  }
  if (options.waitForInput !== false) {
    await expect(input).toBeEnabled({ timeout: 90000 })
  }
  await bubble.scrollIntoViewIfNeeded()
  const assistant = await bubble.innerText()
  await pause(page, 1700)
  return { user: message, assistant }
}

async function sendPublicMessage(page, message, expectedText) {
  const input = page.getByPlaceholder('Describe what you need done')
  const button = page.getByRole('button', { name: 'Send message' })
  await expect(input).toBeEnabled({ timeout: 90000 })
  const assistantMessages = page.locator('[data-testid="message-bubble"][data-message-role="assistant"]')
  const before = await assistantMessages.count()
  await input.fill('')
  await input.type(message, { delay: publicTypingDelayMs })
  await pause(page, 650)
  await button.click()
  const bubble = assistantMessages.nth(before)
  await waitForExpectedText(bubble, expectedText, 180000)
  await expect(input).toBeEnabled({ timeout: 120000 })
  await bubble.scrollIntoViewIfNeeded()
  const text = await bubble.innerText()
  await pause(page, 2200)
  return { user: message, assistant: text }
}

async function waitForExpectedText(locator, expected, timeout) {
  if (Array.isArray(expected)) {
    const started = Date.now()
    while (Date.now() - started < timeout) {
      const text = await locator.innerText().catch(() => '')
      if (expected.some((value) => text.toLowerCase().includes(String(value).toLowerCase()))) return
      await new Promise((resolve) => setTimeout(resolve, 500))
    }
    throw new Error(`Timed out waiting for one of ${JSON.stringify(expected)} in: ${await locator.innerText().catch(() => '')}`)
  }
  await expect(locator).toContainText(expected, { timeout })
}

async function apiGet(pathname, token) {
  const response = await fetch(`${apiAppUrl}${pathname}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    throw new Error(`GET ${pathname} failed: ${response.status} ${await response.text()}`)
  }
  return await response.json()
}

async function apiGetPublic(pathname) {
  const response = await fetch(`${apiAppUrl}${pathname}`)
  if (!response.ok) {
    throw new Error(`GET ${pathname} failed: ${response.status} ${await response.text()}`)
  }
  return await response.json()
}

async function waitForDeploymentLive(evidence) {
  if (!ownerToken) throw new Error('Owner token is required before checking deployment state.')
  const started = Date.now()
  let lastError = null
  while (Date.now() - started < 60_000) {
    try {
      const deployment = await apiGet(`/api/saas-agents/${evidence.agentId}/deployment`, ownerToken)
      if (
        deployment.enabled === true &&
        deployment.visitor_auth_mode === 'anonymous' &&
        deployment.execution_mode === 'sandbox' &&
        deployment.default_write_policy === 'confirm'
      ) {
        const profile = await apiGetPublic(`/api/deployed-agents/${evidence.agentSlug}`)
        if (profile.enabled === true && profile.auth_required === false) {
          evidence.deploymentProof = { deployment, profile }
          return
        }
      }
      lastError = new Error(`Deployment not live yet: ${JSON.stringify(deployment)}`)
    } catch (error) {
      lastError = error
    }
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }
  throw lastError || new Error('Deployment did not become live.')
}

async function fillOperationField(container, field, value) {
  const target = container.locator(`[data-qa-field="${field}"]`)
  await expect(target).toHaveCount(1)
  await target.fill('')
  await target.type(value, { delay: fieldTypingDelayMs })
}

async function selectOperationField(container, field, value) {
  const target = container.locator(`[data-qa-field="${field}"]`)
  await expect(target).toHaveCount(1)
  await target.selectOption(value)
}

async function setOperationCheckbox(container, field, checked) {
  const target = container.locator(`[data-qa-field="${field}"]`)
  await expect(target).toHaveCount(1)
  if (await target.isChecked() !== checked) {
    await target.setChecked(checked)
  }
}

async function humanFill(locator, value) {
  await expect(locator).toBeVisible({ timeout: 30000 })
  await locator.fill('')
  await locator.type(value, { delay: formTypingDelayMs })
}

async function clickWithFallback(locator, label) {
  await expect(locator).toBeVisible({ timeout: 30000 })
  try {
    await locator.click({ timeout: 15000 })
  } catch (error) {
    console.warn(`Pointer click failed for ${label}; using DOM click fallback: ${String(error).split('\n')[0]}`)
    await locator.evaluate((element) => element.click())
  }
}

async function screenshot(page, evidence, name) {
  const file = path.join(screenshotDir, name)
  await page.screenshot({ path: file, fullPage: false })
  evidence.screenshots.push(file)
  await pause(page, 1100)
}

async function waitForCorpusReady(page) {
  await expect(page.getByTestId('corpus-inline-status')).toContainText('Ready', { timeout: 90000 })
}

async function waitForCorpusSettled(page) {
  await page.waitForFunction(() => {
    const status = document.querySelector('[data-testid="corpus-inline-status"]')?.textContent || ''
    return !['Thinking', 'Navigating', 'Opening surface', 'Committing', 'Running diagnostics'].some((value) =>
      status.includes(value),
    )
  }, null, { timeout: 90000 })
}

async function pause(page, ms) {
  const scaled = Number.isFinite(pauseScale) ? Math.max(0, Math.round(ms * pauseScale)) : ms
  await page.waitForTimeout(scaled)
}

function numberFromEnv(name, fallback) {
  const parsed = Number(process.env[name])
  return Number.isFinite(parsed) ? parsed : fallback
}

async function closeBrowserSession({ browser, context, page }) {
  if (process.env.DEMO_KEEP_BROWSER_OPEN === '1') {
    if (cdpEndpoint) {
      await browser?.close().catch(() => undefined)
    }
    return
  }
  if (cdpEndpoint) {
    await page?.close().catch(() => undefined)
    await browser?.close().catch(() => undefined)
    return
  }
  await context?.close().catch(() => undefined)
  await browser?.close().catch(() => undefined)
}

function parseAgentId(url) {
  const match = url.match(/\/app\/agents\/([^/?#]+)/)
  return match ? match[1] : null
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
