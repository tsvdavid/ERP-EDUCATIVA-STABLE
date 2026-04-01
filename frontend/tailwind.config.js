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
            },
            colors: {
                primary: {
                    DEFAULT: '#063e9b', // Eduka360 Core Blue
                    50: '#edf4ff',
                    100: '#dceaff',
                    200: '#b5d3ff',
                    300: '#83b4ff',
                    400: '#4f8fff',
                    500: '#2669fc',
                    600: '#124bec',
                    700: '#063e9b',
                    800: '#053180',
                    900: '#092c7b',
                },
                // Override indigo globally to match our brand
                indigo: {
                    50: '#edf4ff',
                    100: '#dceaff',
                    200: '#b5d3ff',
                    300: '#83b4ff',
                    400: '#4f8fff',
                    500: '#2669fc',
                    600: '#124bec',
                    700: '#063e9b',
                    800: '#053180',
                    900: '#092c7b',
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
