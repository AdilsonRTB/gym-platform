"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useGestao } from "@/lib/cliente";
import { dataCurta } from "@/lib/datas";
import type { Pagina, SocioResumo } from "@/lib/gestaoTypes";

import { Icon } from "../Icon";
import { EstadoSocio } from "./Estados";

const FILTROS = [
  { id: "", nome: "Todos" },
  { id: "ativo", nome: "Ativos" },
  { id: "atraso", nome: "Em atraso" },
  { id: "suspenso", nome: "Suspensos" },
  { id: "inativo", nome: "Inativos" },
];

export function ListaSocios() {
  const router = useRouter();
  const params = useSearchParams();
  const estado = params.get("estado") ?? "";
  const [q, setQ] = useState(params.get("q") ?? "");
  const [pesquisa, setPesquisa] = useState(q);
  const [pagina, setPagina] = useState(1);

  useEffect(() => {
    const t = setTimeout(() => {
      setPesquisa(q);
      setPagina(1);
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  const query = new URLSearchParams({ q: pesquisa, estado, page: String(pagina) });
  const { dados, aCarregar } = useGestao<Pagina<SocioResumo>>(`socios?${query}`);
  const total = dados?.count ?? 0;

  return (
    <>
      <div className="p-head">
        <div>
          <h1>Sócios</h1>
          <p>{aCarregar ? "A carregar…" : `${total} ${total === 1 ? "sócio" : "sócios"}`}</p>
        </div>
        <Link href="/gestao/socios/novo" className="btn btn--sm">
          <Icon name="plus" size={16} /> Novo sócio
        </Link>
      </div>

      <div className="filtros">
        <div className="pesquisa">
          <Icon name="pesquisa" size={18} />
          <input
            className="input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Nome, telefone, email ou nº de sócio"
            aria-label="Pesquisar sócios"
          />
        </div>
      </div>
      <div className="filtros" role="group" aria-label="Filtrar por estado">
        {FILTROS.map((f) => (
          <button
            key={f.id}
            className="chip"
            aria-pressed={estado === f.id}
            onClick={() => {
              setPagina(1);
              router.replace(f.id ? `/gestao/socios?estado=${f.id}` : "/gestao/socios");
            }}
          >
            {f.nome}
          </button>
        ))}
      </div>

      <section className="bloco">
        {dados && dados.results.length === 0 && <div className="bloco__vazio">Nenhum sócio encontrado.</div>}
        <ul className="lista">
          {dados?.results.map((s) => (
            <li key={s.id}>
              <Link href={`/gestao/socios/${s.id}`} className="linha">
                <span className="avatar" aria-hidden="true">
                  {s.numero}
                </span>
                <span className="linha__principal">
                  <strong>{s.nome}</strong>
                  <span>
                    {s.assinatura ? `${s.assinatura.plano} · até ${dataCurta(s.assinatura.data_fim)} · ` : ""}
                    {s.telefone || s.email || "Sem contacto"}
                  </span>
                </span>
                <span className="linha__lado so-desktop" style={{ minWidth: 110 }}>
                  {s.assinatura ? s.assinatura.plano : "—"}
                  <small>{s.assinatura ? `até ${dataCurta(s.assinatura.data_fim)}` : "sem assinatura"}</small>
                </span>
                <EstadoSocio s={s} />
              </Link>
            </li>
          ))}
        </ul>
        {total > 30 && (
          <div className="paginacao">
            <span>
              Página {pagina} de {Math.ceil(total / 30)}
            </span>
            <span style={{ display: "flex", gap: 8 }}>
              <button className="btn btn--sm btn--ghost" disabled={!dados?.previous} onClick={() => setPagina((p) => p - 1)}>
                Anterior
              </button>
              <button className="btn btn--sm btn--ghost" disabled={!dados?.next} onClick={() => setPagina((p) => p + 1)}>
                Seguinte
              </button>
            </span>
          </div>
        )}
      </section>
    </>
  );
}
