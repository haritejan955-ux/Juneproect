/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        severity: {
          none: "#16a34a",
          minor: "#65a30d",
          moderate: "#d97706",
          major: "#dc2626",
          contraindicated: "#7f1d1d",
        },
      },
    },
  },
  plugins: [],
};
