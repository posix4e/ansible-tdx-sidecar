/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        tdx: {
          primary: '#0071C5',
          success: '#16A34A',
          warning: '#EAB308',
          error: '#DC2626',
        },
      },
    },
  },
  plugins: [],
};
