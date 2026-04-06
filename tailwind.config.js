/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./*.py"],
  theme: {
    extend: {
      colors: {
        emerald: {
          50: '#ecfdf5',
          100: '#d1fae5',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
        },
        amber: {
          300: '#fcd34d',
          400: '#fbbf24',
        }
      },
      fontFamily: {
        sans: ['Poppins', 'sans-serif'],
      },
      borderRadius: {
        '3xl': '1.5rem',
      }
    }
  }
}
