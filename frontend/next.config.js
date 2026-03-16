/** @type {import('next').NextConfig} */
const nextConfig = {
  // basePath 由 docker build-arg BASE_PATH 注入，本地为空字符串
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
  output: 'standalone',
}

module.exports = nextConfig
