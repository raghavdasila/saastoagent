import fs from 'node:fs/promises'
import path from 'node:path'

import { chromium } from '@playwright/test'

const endpoint = process.env.DEMO_CDP_ENDPOINT || 'http://host.docker.internal:9223'
const outputRoot = process.env.DEMO_SCREENCAST_ROOT || '/app/recordings/cdp-screencast'
const stopFile = process.env.DEMO_SCREENCAST_STOP_FILE || path.join(outputRoot, 'stop.txt')
const manifestPath = path.join(outputRoot, 'frames.json')
const concatPath = path.join(outputRoot, 'frames.ffconcat')
const framesDir = path.join(outputRoot, 'frames')
const targetFps = Number(process.env.DEMO_SCREENCAST_FPS || '30')
const quality = Number(process.env.DEMO_SCREENCAST_QUALITY || '82')
const maxWidth = Number(process.env.DEMO_SCREENCAST_WIDTH || '1920')
const maxHeight = Number(process.env.DEMO_SCREENCAST_HEIGHT || '1080')

async function exists(file) {
  try {
    await fs.access(file)
    return true
  } catch {
    return false
  }
}

function concatEscape(file) {
  return file.replaceAll("'", "'\\''")
}

async function writeConcat(frames) {
  const lines = ['ffconcat version 1.0']
  for (let index = 0; index < frames.length; index += 1) {
    const frame = frames[index]
    const next = frames[index + 1]
    const duration = next
      ? Math.min(Math.max(next.timestamp - frame.timestamp, 1 / 60), 2)
      : 1 / targetFps
    lines.push(`file '${concatEscape(path.relative(outputRoot, frame.path).replaceAll('\\', '/'))}'`)
    lines.push(`duration ${duration.toFixed(6)}`)
  }
  if (frames.length) {
    const last = frames[frames.length - 1]
    lines.push(`file '${concatEscape(path.relative(outputRoot, last.path).replaceAll('\\', '/'))}'`)
  }
  await fs.writeFile(concatPath, `${lines.join('\n')}\n`)
}

async function main() {
  await fs.mkdir(framesDir, { recursive: true })
  await fs.rm(stopFile, { force: true })

  const browser = await chromium.connectOverCDP(endpoint)
  const context = browser.contexts()[0] || await browser.newContext()
  const page = context.pages()[0] || await context.newPage()
  const session = await context.newCDPSession(page)
  const frames = []
  let frameIndex = 0
  let writing = Promise.resolve()

  session.on('Page.screencastFrame', (event) => {
    const frameNumber = frameIndex
    frameIndex += 1
    const framePath = path.join(framesDir, `frame_${String(frameNumber).padStart(6, '0')}.jpg`)
    const timestamp = Number(event.metadata?.timestamp || Date.now() / 1000)
    frames.push({ index: frameNumber, path: framePath, timestamp })
    writing = writing
      .then(() => fs.writeFile(framePath, Buffer.from(event.data, 'base64')))
      .then(() => session.send('Page.screencastFrameAck', { sessionId: event.sessionId }))
      .catch((error) => {
        console.error(error)
      })
  })

  await session.send('Page.startScreencast', {
    format: 'jpeg',
    quality,
    maxWidth,
    maxHeight,
    everyNthFrame: 1,
  })

  const started = Date.now()
  while (!(await exists(stopFile))) {
    await new Promise((resolve) => setTimeout(resolve, 200))
  }
  await session.send('Page.stopScreencast').catch(() => undefined)
  await writing
  await writeConcat(frames)
  await fs.writeFile(manifestPath, JSON.stringify({ endpoint, outputRoot, frames, elapsedMs: Date.now() - started }, null, 2))
  console.log(JSON.stringify({ ok: true, outputRoot, frames: frames.length, concatPath, manifestPath }, null, 2))
  process.exit(0)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
