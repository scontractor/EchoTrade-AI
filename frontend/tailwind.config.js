/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        t: {
          bg:       '#060608',
          surface:  '#0c0d10',
          panel:    '#101218',
          border:   '#1a1d24',
          orange:   '#f56a00',
          'orange-dim': '#7a3500',
          gold:     '#d4940a',
          green:    '#16c96e',
          'green-dim': '#0a6638',
          red:      '#f03c3c',
          'red-dim':'#7a1e1e',
          blue:     '#3b8eff',
          'blue-dim':'#1a4480',
          yellow:   '#e6b800',
          purple:   '#9966ff',
          cyan:     '#00c8e6',
          text:     '#c8cdd8',
          muted:    '#6b7280',
          dim:      '#374151',
          faint:    '#1f2937',
        },
      },
      fontFamily: {
        mono:  ['"IBM Plex Mono"', '"JetBrains Mono"', 'Consolas', 'monospace'],
        sans:  ['"Inter"', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },
      animation: {
        ticker:       'ticker 45s linear infinite',
        blink:        'blink 1.1s step-end infinite',
        'fade-up':    'fadeUp 0.25s ease-out',
        'bounce-dot': 'bounceDot 1s ease-in-out infinite',
      },
      keyframes: {
        ticker:    { '0%': { transform: 'translateX(0)' }, '100%': { transform: 'translateX(-50%)' } },
        blink:     { '0%,100%': { opacity: '1' }, '50%': { opacity: '0' } },
        fadeUp:    { from: { opacity: '0', transform: 'translateY(6px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        bounceDot: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-5px)' } },
      },
    },
  },
  plugins: [],
}
