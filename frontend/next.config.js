/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output standalone untuk Docker deployment (ukuran image lebih kecil)
  output: "standalone",

  // Proxy /api/v1/* ke backend — fallback jika Nginx tidak handle routing
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://backend:8000/api/v1/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
