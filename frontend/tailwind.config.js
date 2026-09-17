/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: '#0F1512',
          900: '#151E1A',
          800: '#1C2622',
          700: '#26332D',
          600: '#354339',
        },
        carbon: {
          400: '#6EE7A8',
          500: '#3DDC84',
          600: '#28B96A',
        },
        energy: {
          400: '#FFC670',
          500: '#F5A623',
          600: '#D6890F',
        },
        alert: {
          500: '#F2664B',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'grid-pulse': "linear-gradient(90deg, transparent 0%, rgba(61,220,132,0.35) 50%, transparent 100%)",
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.45s ease both',
        'fade-in': 'fadeIn 0.3s ease both',
        'pulse-dot': 'pulseDot 1.8s ease-in-out infinite',
        shimmer: 'shimmer 1.6s linear infinite',
      },
    },
  },
  plugins: [],
}
