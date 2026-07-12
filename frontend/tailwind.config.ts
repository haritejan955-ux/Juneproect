import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        approved: "#16a34a",
        denied: "#dc2626",
        partial: "#d97706",
      },
    },
  },
  plugins: [],
};

export default config;
