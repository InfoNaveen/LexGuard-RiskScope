/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        lex: {
          sidebar: "#0f1117",
          danger: "#A32D2D",
          warning: "#BA7517",
          medium: "#854F0B",
          success: "#3B6D11",
          info: "#185FA5",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        audit: "0 18px 48px rgba(15, 17, 23, 0.09)",
      },
    },
  },
  plugins: [],
};
