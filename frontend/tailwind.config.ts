import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0e14",
        card: "#121721",
        "card-border": "#1e2638",
        terminal: {
          dark: "#080a0f",
          accent: "#2563eb",
          bullish: "#10b981",
          bearish: "#ef4444",
          neutral: "#64748b",
          warning: "#f59e0b",
        }
      },
    },
  },
  plugins: [],
};
export default config;
