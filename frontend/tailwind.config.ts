import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './lib/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                primary:   { DEFAULT: '#4F46E5', dark: '#4338CA', light: '#6366F1', surface: 'rgba(79,70,229,0.08)' },
                secondary: { DEFAULT: '#2563EB', dark: '#1D4ED8', surface: 'rgba(37,99,235,0.08)' },
                teal:      { DEFAULT: '#14B8A6', dark: '#0F766E' },
                violet:    { DEFAULT: '#8B5CF6', dark: '#7C3AED' },
                success:   { DEFAULT: '#10B981', dark: '#065F46', surface: 'rgba(16,185,129,0.10)' },
                warning:   { DEFAULT: '#F59E0B', dark: '#92400E' },
                danger:    { DEFAULT: '#EF4444', dark: '#B91C1C' },
                surface: {
                    app:     '#F8FAFC',
                    card:    '#FFFFFF',
                    sidebar: '#F1F5F9',
                },
                slate: {
                    50:  '#F8FAFC',
                    100: '#F1F5F9',
                    200: '#E2E8F0',
                    300: '#CBD5E1',
                    400: '#94A3B8',
                    500: '#64748B',
                    600: '#475569',
                    700: '#334155',
                    800: '#1E293B',
                    900: '#0F172A',
                },
            },
            boxShadow: {
                'card':     '0 1px 3px rgba(15,23,42,0.07), 0 1px 2px rgba(15,23,42,0.04)',
                'hover':    '0 4px 16px rgba(15,23,42,0.09), 0 2px 6px rgba(15,23,42,0.05)',
                'md':       '0 8px 24px rgba(15,23,42,0.10), 0 3px 8px rgba(15,23,42,0.06)',
                'lg':       '0 16px 40px rgba(15,23,42,0.12), 0 4px 12px rgba(15,23,42,0.07)',
                'tooltip':  '0 8px 24px rgba(15,23,42,0.10)',
                'primary':  '0 2px 12px rgba(79,70,229,0.30)',
            },
            borderRadius: {
                'xl':  '12px',
                '2xl': '16px',
                '3xl': '22px',
            },
            animation: {
                'fade-in':  'fadeIn 0.2s ease-out',
                'slide-up': 'slideUp 0.25s cubic-bezier(0.16,1,0.3,1)',
                'scale-in': 'scaleIn 0.18s cubic-bezier(0.16,1,0.3,1)',
                'shimmer':  'shimmer 1.8s ease-in-out infinite',
            },
            keyframes: {
                fadeIn:  { '0%': { opacity:'0' },                             '100%': { opacity:'1' } },
                slideUp: { '0%': { transform:'translateY(8px)', opacity:'0' },'100%': { transform:'translateY(0)', opacity:'1' } },
                scaleIn: { '0%': { transform:'scale(0.97)', opacity:'0' },    '100%': { transform:'scale(1)', opacity:'1' } },
                shimmer: { '0%': { backgroundPosition:'-400% 0' },            '100%': { backgroundPosition:'400% 0' } },
            },
        },
    },
    plugins: [],
}

export default config
