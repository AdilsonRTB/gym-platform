import "./painel.css";

import type { Metadata } from "next";

import { RegistarSW } from "@/components/RegistarSW";

// Dados privados (sessão): nunca em cache partilhada.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: { default: "Gestão", template: "%s · Gestão" },
  robots: { index: false, follow: false },
};

export default function GestaoLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <RegistarSW />
    </>
  );
}
