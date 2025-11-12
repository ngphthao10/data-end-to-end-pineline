/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://flask-api:5000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
