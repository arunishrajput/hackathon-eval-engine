/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#450a0a',
          950: '#3b0808',
        },
        dark: {
          DEFAULT: '#13141a',
          card: '#1c1d25',
          elevated: '#252630',
          border: '#2d2e3a',
          muted: '#3a3b48',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
        'gradient-dark': 'linear-gradient(180deg, #1c1d25 0%, #13141a 100%)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      boxShadow: {
        'glow-brand': '0 0 20px rgba(177, 54, 30, 0.2)',
        'glow-sm': '0 0 10px rgba(177, 54, 30, 0.12)',
      },
    },
  },
  plugins: [],
};
