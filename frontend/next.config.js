/** @type {import('next').NextConfig} */
const nextConfig = {
  // Output standalone untuk Docker deployment (ukuran image lebih kecil)
  output: "standalone",
};

module.exports = nextConfig;
