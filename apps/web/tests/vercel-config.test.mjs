import assert from 'node:assert/strict'
import { test } from 'node:test'

test('Vercel rewrites API requests from the web project to the configured origin', async (t) => {
  const previous = process.env.API_ORIGIN
  t.after(() => {
    if (previous === undefined) delete process.env.API_ORIGIN
    else process.env.API_ORIGIN = previous
  })

  process.env.API_ORIGIN = 'https://preview-api.example.com/'
  const preview = await import('../vercel.ts?preview')
  assert.deepEqual(preview.config.rewrites, [{
    source: '/api/:path*',
    destination: 'https://preview-api.example.com/:path*',
  }])

  process.env.API_ORIGIN = 'https://production-api.example.com'
  const production = await import('../vercel.ts?production')
  assert.equal(production.config.rewrites[0].destination, 'https://production-api.example.com/:path*')

  for (const [index, origin] of [
    'http://api.example.com',
    'https://api.example.com/api',
    'https://api.example.com/?query=value',
    'not a URL',
  ].entries()) {
    process.env.API_ORIGIN = origin
    await assert.rejects(import(`../vercel.ts?invalid=${index}`), /API_ORIGIN must be/)
  }

  delete process.env.API_ORIGIN
  await assert.rejects(import('../vercel.ts?missing'), /Set API_ORIGIN/)
})
