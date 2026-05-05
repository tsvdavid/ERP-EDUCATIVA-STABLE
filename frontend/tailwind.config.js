/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                display: ['Outfit', 'sans-serif'],
            },
            colors: {
                primary: {
                    DEFAULT: '#E11D48', // Eduka360 Rose/Red
                    50: '#fff1f2',
                    100: '#ffe4e6',
                    200: '#fecdd3',
                    300: '#fda4af',
                    400: '#fb7185',
                    500: '#f43f5e',
                    600: '#e11d48',
                    700: '#be123c',
                    800: '#9f1239',
                    900: '#881337',
                    950: '#4c0519',
                },
                // Override indigo globally to match our brand
                indigo: {
                    50: '#fff1f2',
                    100: '#ffe4e6',
                    200: '#fecdd3',
                    300: '#fda4af',
                    400: '#fb7185',
                    500: '#f43f5e',
                    600: '#e11d48',
                    700: '#be123c',
                    800: '#9f1239',
                    900: '#881337',
                    950: '#4c0519',
                },
                accent: {
                    yellow: '#facc15', // Gold from Owl
                    red: '#ef4444',    // Red from Owl
                    blue: '#1d4ed8',   // Deeper blue
                },
                secondary: '#64748b', // Slate 500
                success: '#10b981', // Emerald 500
                warning: '#f59e0b', // Amber 500
                danger: '#ef4444',  // Red 500
            }
        },
    },
    plugins: [],
}
