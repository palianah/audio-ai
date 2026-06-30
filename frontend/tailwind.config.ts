import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        editor: {
          bg: "#1a1a2e",
          surface: "#16213e",
          track: "#0f3460",
          accent: "#e94560",
          waveform: "#53d769",
          text: "#eaeaea",
          muted: "#7a7a8e",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
