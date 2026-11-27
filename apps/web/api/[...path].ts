function getApiOrigin(): URL {
  const url = new URL(process.env.API_ORIGIN?.trim() ?? '')
  if (
    url.protocol !== 'https:' || url.username || url.password ||
    url.pathname !== '/' || url.search || url.hash
  ) {
    throw new Error('API_ORIGIN must be an HTTPS origin.')
  }
  return url
}

export default {
  async fetch(request: Request): Promise<Response> {
    let target: URL
    try {
      target = getApiOrigin()
    } catch {
      return Response.json({ detail: 'API_ORIGIN is missing or invalid.' }, { status: 503 })
    }

    const incoming = new URL(request.url)
    target.pathname = incoming.pathname.slice('/api'.length)
    target.search = incoming.search

    try {
      const contentType = request.headers.get('content-type')
      const upstream = await fetch(target, {
        method: request.method,
        headers: contentType ? { 'content-type': contentType } : undefined,
        body: request.body ? await request.arrayBuffer() : undefined,
        redirect: 'error',
        signal: request.signal,
      })
      const headers = new Headers({ 'cache-control': 'no-store' })
      for (const name of ['content-type', 'retry-after']) {
        const value = upstream.headers.get(name)
        if (value !== null) headers.set(name, value)
      }
      return new Response(upstream.body, { status: upstream.status, headers })
    } catch {
      return Response.json({ detail: 'Could not reach the API.' }, { status: 502 })
    }
  },
}
