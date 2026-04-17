/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#f59e0b",
          hover: "#d97706",
          pressed: "#b45309",
          ghost: "rgba(245,158,11,0.10)",
        },
        up: "#22c55e",
        down: "#ef4444",
        warn: "#eab308",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Geist Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        DEFAULT: "4px",
        md: "6px",
        lg: "8px",
      },
      fontSize: {
        micro: ["11px", { lineHeight: "1.4", letterSpacing: "0.02em" }],
      },
      boxShadow: {
        etched: "inset 0 1px 0 rgb(255 255 255 / 0.04)",
      },
      keyframes: {
        'pulse-dot': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
        'cell-flash': {
          '0%': { backgroundColor: 'rgba(245,158,11,0.2)' },
          '100%': { backgroundColor: 'transparent' },
        },
      },
      animation: {
        'pulse-dot': 'pulse-dot 1.4s ease-in-out infinite',
        'cell-flash': 'cell-flash 600ms ease-out',
      },
    },
  },
  plugins: [],
};
