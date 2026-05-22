import http from 'node:http'

const port = Number(process.env.MOCK_STOREFRONT_PORT || 9109)
let adminWrites = 0

const products = [
  { id: 'prod_1', title: 'Sandbox Hoodie', handle: 'sandbox-hoodie', status: 'published' },
  { id: 'prod_2', title: 'Sandbox Mug', handle: 'sandbox-mug', status: 'published' },
]

function sendJson(res, status, body) {
  res.writeHead(status, {
    'content-type': 'application/json',
    'access-control-allow-origin': '*',
    'access-control-allow-headers': 'authorization,content-type',
    'access-control-allow-methods': 'GET,POST,OPTIONS',
  })
  res.end(JSON.stringify(body))
}

function storefrontSpec(origin) {
  return {
    openapi: '3.0.0',
    info: { title: 'Sandbox Storefront API', version: '1.0.0' },
    servers: [{ url: origin }],
    paths: {
      '/products': {
        get: {
          operationId: 'listProducts',
          tags: ['Products'],
          summary: 'List products',
          responses: { 200: { description: 'OK' } },
        },
      },
      '/products/{product_id}': {
        get: {
          operationId: 'getProduct',
          tags: ['Products'],
          summary: 'Get product',
          parameters: [
            { name: 'product_id', in: 'path', required: true, schema: { type: 'string' } },
          ],
          responses: { 200: { description: 'OK' } },
        },
      },
    },
  }
}

function adminSpec(origin) {
  return {
    openapi: '3.0.0',
    info: { title: 'Sandbox Admin API', version: '1.0.0' },
    servers: [{ url: origin }],
    paths: {
      '/admin/products': {
        post: {
          operationId: 'createProduct',
          tags: ['Admin Products'],
          summary: 'Create product',
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['title'],
                  properties: { title: { type: 'string' } },
                },
              },
            },
          },
          responses: { 200: { description: 'OK' } },
        },
      },
    },
  }
}

const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') return sendJson(res, 204, {})
  const origin = `http://host.docker.internal:${port}`
  const url = new URL(req.url || '/', `http://localhost:${port}`)

  if (url.pathname === '/__fixture/reset' && req.method === 'POST') {
    adminWrites = 0
    return sendJson(res, 200, { ok: true })
  }
  if (url.pathname === '/__fixture/admin-writes') {
    return sendJson(res, 200, { count: adminWrites })
  }
  if (url.pathname === '/openapi.json') {
    return sendJson(res, 200, storefrontSpec(origin))
  }
  if (url.pathname === '/admin/openapi.json') {
    return sendJson(res, 200, adminSpec(origin))
  }
  if (url.pathname === '/products') {
    return sendJson(res, 200, { products })
  }
  if (url.pathname.startsWith('/products/')) {
    const product = products.find((item) => item.id === url.pathname.split('/').pop())
    return sendJson(res, product ? 200 : 404, product ? { product } : { error: 'not_found' })
  }
  if (url.pathname === '/admin/products' && req.method === 'POST') {
    if (req.headers.authorization !== 'Bearer e2e-admin-token') {
      return sendJson(res, 401, { error: 'unauthorized' })
    }
    adminWrites += 1
    return sendJson(res, 200, { product: { id: `prod_admin_${adminWrites}`, status: 'draft' } })
  }
  return sendJson(res, 404, { error: 'not_found' })
})

server.listen(port, '0.0.0.0', () => {
  console.log(`mock-storefront-api listening on ${port}`)
})

process.on('SIGTERM', () => server.close(() => process.exit(0)))
process.on('SIGINT', () => server.close(() => process.exit(0)))
