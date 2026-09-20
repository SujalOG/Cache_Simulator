/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          dark: '#0a0d14',
          card: '#111622',
          border: '#1e293b',
          accent: '#38bdf8',
          green: '#10b981',
          rose: '#f43f5e',
          amber: '#f59e0b',
        }
      }
    },
  },
  plugins: [],
}
