import http from 'node:http'
import net from 'node:net'

const listenPort = Number(process.env.CDP_PROXY_PORT || '9223')
const targetHost = process.env.CDP_TARGET_HOST || '::1'
const targetPort = Number(process.env.CDP_TARGET_PORT || '9222')

function rewriteDebuggerUrls(body, publicHost) {
  return body
    .replaceAll(`ws://127.0.0.1:${targetPort}`, `ws://${publicHost}`)
    .replaceAll(`ws://localhost:${targetPort}`, `ws://${publicHost}`)
    .replaceAll(`ws://[::1]:${targetPort}`, `ws://${publicHost}`)
}

const server = http.createServer((request, response) => {
  const upstream = http.request(
    {
      host: targetHost,
      port: targetPort,
      method: request.method,
      path: request.url,
      headers: {
        ...request.headers,
        host: `127.0.0.1:${targetPort}`,
      },
    },
    (upstreamResponse) => {
      const chunks = []
      upstreamResponse.on('data', (chunk) => chunks.push(chunk))
      upstreamResponse.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf8')
        const publicHost = request.headers.host || `127.0.0.1:${listenPort}`
        const rewritten = rewriteDebuggerUrls(body, publicHost)
        const headers = {
          ...upstreamResponse.headers,
          'content-length': Buffer.byteLength(rewritten),
        }
        response.writeHead(upstreamResponse.statusCode || 502, headers)
        response.end(rewritten)
      })
    },
  )
  upstream.on('error', (error) => {
    response.writeHead(502, { 'content-type': 'text/plain' })
    response.end(String(error?.stack || error))
  })
  request.pipe(upstream)
})

server.on('upgrade', (request, socket, head) => {
  const upstream = net.connect(targetPort, targetHost, () => {
    const headerLines = [`${request.method} ${request.url} HTTP/${request.httpVersion}`]
    for (const [name, value] of Object.entries(request.headers)) {
      headerLines.push(`${name === 'host' ? 'Host' : name}: ${name === 'host' ? `127.0.0.1:${targetPort}` : value}`)
    }
    upstream.write(`${headerLines.join('\r\n')}\r\n\r\n`)
    if (head?.length) {
      upstream.write(head)
    }
    socket.pipe(upstream)
    upstream.pipe(socket)
  })
  upstream.on('error', () => socket.destroy())
})

server.listen(listenPort, '0.0.0.0', () => {
  console.log(JSON.stringify({ listening: listenPort, targetHost, targetPort }))
})
