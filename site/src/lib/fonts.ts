import { Archivo, DM_Sans, Fraunces, Inter, Manrope, Space_Grotesk } from "next/font/google";

// Todas as fontes disponíveis no Admin; o browser só descarrega as que o tema usa.
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap", preload: false });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope", display: "swap", preload: false });
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
  preload: false,
});
const archivo = Archivo({ subsets: ["latin"], variable: "--font-archivo", display: "swap", preload: false });
const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-fraunces", display: "swap", preload: false });
const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans", display: "swap", preload: false });

export const fontVariables = [inter, manrope, spaceGrotesk, archivo, fraunces, dmSans]
  .map((f) => f.variable)
  .join(" ");
