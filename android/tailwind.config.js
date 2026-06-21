/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./App.{ts,tsx}', './src/**/*.{ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        muted: '#6b7280',
        background: '#f9fafb',
        card: '#ffffff',
        border: '#e5e7eb',
        destructive: '#ef4444',
        success: '#22c55e',
      },
    },
  },
  plugins: [],
};
