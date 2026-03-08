import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        jie: {
          bg: "#0b1220",
          card: "#13203a",
          accent: "#ff7b39",
          success: "#33d17a",
          muted: "#8da1c7"
        }
      }
    }
  },
  plugins: []
};

export default config;
