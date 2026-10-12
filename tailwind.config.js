/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        // Monochrome editorial palette. Semantic names remain for template compatibility.
        parchment: {
          DEFAULT: "#FFFFFF",
          light: "#FFFFFF",
          deep: "#F5F5F5",
        },
        wine: {
          DEFAULT: "#111111",
          dark: "#000000",
          light: "#333333",
        },
        gold: {
          DEFAULT: "#777777",
          dark: "#444444",
          light: "#AAAAAA",
        },
        indigo_accent: "#111111",
        ink: {
          DEFAULT: "#111111",
          muted: "#666666",
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
