/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#090A0F",
        surface: "#12141F",
        "surface-border": "#1E2235",
        "surface-hover": "#1A1D2D",
        primary: {
          DEFAULT: "#6366F1",
          hover: "#4F46E5",
          glow: "rgba(99, 102, 241, 0.25)"
        },
        accent: {
          cyan: "#06B6D4",
          violet: "#8B5CF6",
          amber: "#F59E0B",
          emerald: "#10B981"
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 15px rgba(99, 102, 241, 0.2)' },
          '100%': { boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)' },
        }
      }
    },
  },
  plugins: [],
};
