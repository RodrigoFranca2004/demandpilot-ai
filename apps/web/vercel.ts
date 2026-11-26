const configuredOrigin = process.env.API_ORIGIN?.trim()

if (!configuredOrigin) {
  throw new Error('Set API_ORIGIN in the Vercel web project for this environment.')
}

let apiUrl: URL
try {
  apiUrl = new URL(configuredOrigin)
} catch {
  throw new Error('API_ORIGIN must be a valid HTTPS origin.')
}

if (
  apiUrl.protocol !== 'https:' ||
  apiUrl.username ||
  apiUrl.password ||
  apiUrl.pathname !== '/' ||
  apiUrl.search ||
  apiUrl.hash
) {
  throw new Error('API_ORIGIN must be an HTTPS origin without credentials, a path, a query, or a fragment.')
}

export const config = {
  framework: 'vite',
  installCommand: 'npm ci',
  buildCommand: 'npm run build',
  outputDirectory: 'dist',
  rewrites: [
    {
      source: '/api/:path*',
      destination: `${apiUrl.origin}/:path*`,
    },
  ],
}
