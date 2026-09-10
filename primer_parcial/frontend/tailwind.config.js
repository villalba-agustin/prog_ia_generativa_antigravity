/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pitch: {
          light: '#22c55e',
          DEFAULT: '#15803d',
          dark: '#14532d',
        }
      }
    },
  },
  plugins: [],
}
