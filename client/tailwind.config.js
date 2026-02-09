/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        'primary-dark': '#2563eb',
        secondary: '#8b5cf6',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        bg: '#0f172a',
        'bg-light': '#1e293b',
        'bg-lighter': '#334155',
        text: '#f1f5f9',
        'text-muted': '#94a3b8',
        border: '#475569',
      },
    },
  },
  plugins: [],
}
