"use client";

import { useRouter } from "next/navigation";

import { pedido } from "@/lib/cliente";

import { Icon } from "../Icon";

export function Sair() {
  const router = useRouter();
  return (
    <button
      className="icon-btn"
      aria-label="Sair"
      title="Sair"
      onClick={async () => {
        await pedido("app", "auth/sair", { corpo: {} });
        router.replace("/app/entrar");
        router.refresh();
      }}
    >
      <Icon name="sair" size={16} />
    </button>
  );
}
