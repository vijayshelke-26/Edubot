/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm "paper" canvas — the scholar's desk
        paper: {
          DEFAULT: "#F4F0E6",
          deep: "#ECE5D5",
        },
        surface: {
          DEFAULT: "#FCFAF4", // warm card white
          raised: "#FFFFFF",
        },
        // Warm near-black inks for text
        ink: {
          DEFAULT: "#211E17",
          soft: "#564F40",
          faint: "#8C8470",
        },
        line: {
          DEFAULT: "#E3DBC8",
          strong: "#D2C8AF",
        },
        // Primary brand — deep pine green (growth, learning)
        brand: {
          50: "#EEF5F0",
          100: "#D6E8DD",
          200: "#AED2BC",
          300: "#7EB496",
          400: "#4F9170",
          500: "#2F7355",
          600: "#235B43",
          700: "#1B4936",
          800: "#163A2C",
          900: "#102A20",
        },
        // Accent — marigold gold highlighter
        accent: {
          50: "#FCF4DE",
          100: "#F7E6B6",
          200: "#F0D079",
          300: "#E9B844",
          400: "#DDA017",
          500: "#C2870F",
          600: "#9C6A0C",
        },
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'Cambria', 'serif'],
        sans: ['"Hanken Grotesk"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        card: "0 1px 2px rgba(33,30,23,0.04), 0 14px 30px -18px rgba(33,30,23,0.22)",
        pop: "0 2px 6px rgba(33,30,23,0.06), 0 24px 48px -22px rgba(33,30,23,0.30)",
        brand: "0 10px 24px -10px rgba(27,73,54,0.45)",
        accent: "0 8px 20px -8px rgba(221,160,23,0.45)",
        inset: "inset 0 1px 0 rgba(255,255,255,0.6)",
      },
      borderRadius: {
        xl: "0.9rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.22, 1, 0.36, 1) both",
        "fade-in": "fade-in 0.5s ease both",
        "scale-in": "scale-in 0.4s cubic-bezier(0.22, 1, 0.36, 1) both",
        float: "float 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
}
