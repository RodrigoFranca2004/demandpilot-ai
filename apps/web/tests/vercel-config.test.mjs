import assert from 'node:assert/strict'
import { test } from 'node:test'
import proxy from '../api/[...path].ts'

test('forwards API paths, queries, POST bodies and response status', async (t) => {
  const previous = process.env.API_ORIGIN
  t.after(() => {
    if (previous === undefined) delete process.env.API_ORIGIN
    else process.env.API_ORIGIN = previous
  })

  process.env.API_ORIGIN = 'https://api.example.com'
  const upstream = t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url.href, 'https://api.example.com/restaurants/1/advisor/chat?horizon=7')
    assert.equal(options.method, 'POST')
    assert.equal(options.headers['content-type'], 'application/json')
    assert.deepEqual(JSON.parse(new TextDecoder().decode(options.body)), { message: 'Hello' })
    return Response.json({ detail: 'Limit reached' }, { status: 429, headers: { 'retry-after': '30' } })
  })

  const response = await proxy.fetch(new Request('https://web.example.com/api/restaurants/1/advisor/chat?horizon=7', {
    method: 'POST',
    body: JSON.stringify({ message: 'Hello' }),
    headers: { 'content-type': 'application/json' },
  }))
  assert.equal(response.status, 429)
  assert.equal(response.headers.get('retry-after'), '30')

  for (const origin of ['', 'http://api.example.com', 'https://api.example.com/api']) {
    process.env.API_ORIGIN = origin
    assert.equal((await proxy.fetch(new Request('https://web.example.com/api/health'))).status, 503)
  }
  assert.equal(upstream.mock.callCount(), 1)
})
