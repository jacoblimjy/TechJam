import type { Config } from "tailwindcss";
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f8ff",
          100: "#e0f0ff",
          200: "#b9deff",
          300: "#8ecbff",
          400: "#5db2ff",
          500: "#2e98ff",
          600: "#157ee6",
          700: "#0f66b8",
          800: "#0a4b85",
          900: "#07345c",
        },
      },
      boxShadow: {
        card: "0 4px 24px rgba(2, 6, 23, 0.08)",
      },
      backgroundImage: {
        'brand-gradient': "linear-gradient(135deg, #2e98ff 0%, #8b5cf6 50%, #06b6d4 100%)",
        // Dark, slightly brighter gold gradient for title
        'grand-title-dark': "linear-gradient(135deg, #c2410c 0%, #f59e0b 38%, #fbbf24 68%, #b45309 100%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
