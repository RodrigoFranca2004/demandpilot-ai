import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'))

test('routes both flat and nested API paths to the configured backend origin', () => {
  const [api, filesystem] = config.routes
  const source = new RegExp(`^${api.src}$`)

  assert.equal(api.dest, '${API_ORIGIN}/$1')
  assert.deepEqual(api.env, ['API_ORIGIN'])
  assert.deepEqual(filesystem, { handle: 'filesystem' })
  for (const path of ['health', 'demo', 'products/1/forecast/metrics', 'restaurants/1/inventory/analysis']) {
    assert.equal(source.exec(`/api/${path}`)?.[1], path)
  }
  assert.equal(source.test('/assets/index.js'), false)
})
