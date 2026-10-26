"use client";

import Link from "next/link";
import { useMemo, useState, useSyncExternalStore } from "react";

import { DIAS, DIAS_CURTOS, diaDeHoje } from "@/lib/format";
import type { Aula } from "@/lib/types";

import { Icon } from "./Icon";

const subscribe = () => () => {};

/** Horário semanal com filtros por dia e modalidade. */
export function Schedule({ aulas }: { aulas: Aula[] }) {
  const hoje = useSyncExternalStore(subscribe, diaDeHoje, () => -1);
  const [escolhido, setEscolhido] = useState<number | null>(null);
  const [modalidade, setModalidade] = useState("");
  const dia = escolhido ?? (hoje < 0 ? 0 : hoje);

  const modalidades = useMemo(() => {
    const mapa = new Map(aulas.map((a) => [a.modalidade.slug, a.modalidade.nome]));
    return [...mapa].sort((a, b) => a[1].localeCompare(b[1], "pt"));
  }, [aulas]);

  const lista = aulas.filter((a) => a.dia_semana === dia && (!modalidade || a.modalidade.slug === modalidade));
  const diasComAulas = new Set(aulas.map((a) => a.dia_semana));

  return (
    <div>
      <div className="schedule-toolbar">
        <div className="day-tabs" role="group" aria-label="Dia da semana">
          {DIAS_CURTOS.map((nome, i) => (
            <button
              key={nome}
              type="button"
              className="chip"
              aria-pressed={i === dia}
              aria-label={DIAS[i]}
              onClick={() => setEscolhido(i)}
              disabled={!diasComAulas.has(i)}
              style={!diasComAulas.has(i) ? { opacity: 0.4 } : undefined}
            >
              {nome}
              {i === hoje && <span className="chip__hoje" title="Hoje" />}
            </button>
          ))}
        </div>
        <label style={{ marginBottom: 24, minWidth: 220 }}>
          <span className="sr-only">Modalidade</span>
          <select className="select" value={modalidade} onChange={(e) => setModalidade(e.target.value)}>
            <option value="">Todas as modalidades</option>
            {modalidades.map(([slug, nome]) => (
              <option key={slug} value={slug}>
                {nome}
              </option>
            ))}
          </select>
        </label>
      </div>

      <h2 className="h3" style={{ margin: "8px 0 16px" }} aria-live="polite">
        {DIAS[dia]}
        {dia === hoje && <span className="badge badge--accent" style={{ marginLeft: 10, verticalAlign: "middle" }}>Hoje</span>}
      </h2>

      {lista.length === 0 ? (
        <div className="empty">Sem aulas para este filtro.</div>
      ) : (
        <ul className="schedule">
          {lista.map((a) => (
            <li key={a.id} className="slot">
              <span className="slot__hora">
                {a.hora_inicio}
                <span className="slot__fim">até {a.hora_fim}</span>
              </span>
              <div>
                <Link href={`/modalidades/${a.modalidade.slug}`} className="slot__nome">
                  {a.modalidade.nome}
                </Link>
                <div className="slot__info">
                  {a.treinador && (
                    <span>
                      <Icon name="user" size={14} />
                      {a.treinador.nome}
                    </span>
                  )}
                  {a.sala && (
                    <span>
                      <Icon name="pin" size={14} />
                      {a.sala}
                    </span>
                  )}
                  {a.lotacao && (
                    <span>
                      <Icon name="pessoas" size={14} />
                      {a.lotacao} lugares
                    </span>
                  )}
                </div>
              </div>
              <div className="slot__acao">
                <Link
                  href={`/contactos?tipo=aula_experimental&modalidade=${a.modalidade.slug}`}
                  className="btn btn--sm btn--ghost"
                >
                  Experimentar
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
