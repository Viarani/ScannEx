/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: { teal: "#0e7c7b", cyan: "#00f2fe", navy: "#0a0e1a" },
      },
    },
  },
  plugins: [],
};
