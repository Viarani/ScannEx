/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_URL || process.env.FLASK_API_URL || "http://127.0.0.1:5000";
    return [
      {
        source: "/api/flask/:path*",
        destination: `${api}/api/:path*`,
      },
    ];
  },
};
export default nextConfig;
