/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        // Warm parchment background family
        parchment: {
          DEFAULT: "#FBF0DE",
          light: "#FDF6EA",
          deep: "#F5E6C8",
        },
        // Primary ink / maroon — headings, primary buttons
        wine: {
          DEFAULT: "#5A1B1E",
          dark: "#411214",
          light: "#7A2C2F",
        },
        // Gold/amber — secondary CTAs, "stay connected" accents
        gold: {
          DEFAULT: "#C68A2E",
          dark: "#A8721E",
          light: "#E0AE5C",
        },
        // Deep navy — used sparingly (e.g. third book's cover treatment)
        indigo_accent: "#1F3A5F",
        ink: {
          DEFAULT: "#3A2E24", // body text
          muted: "#6B5D4F",   // secondary text
        },
      },
      fontFamily: {
        display: ["'Cormorant Garamond'", "serif"], // headlines, logo
        body: ["'Lora'", "serif"],                   // paragraph copy
        sans: ["'Inter'", "sans-serif"],              // nav, buttons, labels
      },
      borderRadius: {
        DEFAULT: "0.375rem",
      },
    },
  },
  plugins: [],
};
