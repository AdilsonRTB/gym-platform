"use client";

import Link from "next/link";
import { useMemo, useSyncExternalStore } from "react";

import { DIAS, diaDeHoje } from "@/lib/format";
import type { Aula } from "@/lib/types";

import { Icon } from "./Icon";

const subscribe = () => () => {};

/** Aulas de hoje (calculado no browser, porque a página é servida em cache). */
export function TodaySchedule({ aulas }: { aulas: Aula[] }) {
  const hoje = useSyncExternalStore(subscribe, diaDeHoje, () => -1);
  const dia = hoje < 0 ? 0 : hoje;
  const lista = useMemo(() => aulas.filter((a) => a.dia_semana === dia), [aulas, dia]);

  return (
    <div>
      <p className="muted" style={{ margin: "0 0 16px" }}>
        {hoje < 0 ? " " : `${DIAS[dia]} · ${lista.length} ${lista.length === 1 ? "aula" : "aulas"}`}
      </p>
      {lista.length === 0 ? (
        <div className="empty">Hoje não há aulas de grupo. A sala está aberta no horário normal.</div>
      ) : (
        <ul className="schedule">
          {lista.slice(0, 6).map((a) => (
            <li key={a.id} className="slot">
              <span className="slot__hora">
                {a.hora_inicio}
                <span className="slot__fim">{a.hora_fim}</span>
              </span>
              <div>
                <div className="slot__nome">{a.modalidade.nome}</div>
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
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
      <div style={{ marginTop: 24 }}>
        <Link href="/horario" className="link-arrow">
          Ver horário completo <Icon name="arrow-right" size={16} />
        </Link>
      </div>
    </div>
  );
}
