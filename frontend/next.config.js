/** @type {import('next').NextConfig} */
const nextConfig = {
    // Silence the "multiple lockfiles" warning from the monorepo root package-lock
    turbopack: {
        root: __dirname,
    },

    // ── API proxy ──────────────────────────────────────────────────────────────
    async rewrites() {
        // In production (Vercel) set BACKEND_URL to the Render service URL.
        // Locally it falls back to localhost:8000.
        const backendUrl = process.env.BACKEND_URL ?? 'http://localhost:8000'
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/api/:path*`,
            },
        ]
    },

    // ── Memory optimisations ───────────────────────────────────────────────────
    // Limit webpack/SWC worker threads so the build never spawns >2 OS threads.
    // On a laptop this is the single biggest lever: webpack defaults to CPU-count
    // workers which can easily allocate 4-8 GB during a cold build.
    experimental: {
        cpus: 1,
        // Reduce peak webpack memory during builds
        webpackMemoryOptimizations: true,
    },

    // Never embed source maps into production bundles — cuts output size and
    // avoids the browser loading multi-MB .map files per page.
    productionBrowserSourceMaps: false,

}

module.exports = nextConfig
