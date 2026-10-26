"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

import { useGestao } from "@/lib/cliente";
import { dataLonga, hora } from "@/lib/datas";
import type { CheckIn } from "@/lib/gestaoTypes";
import {
  atualizarSnapshot,
  fila,
  procurarLocal,
  registarEntrada,
  type ResultadoEntrada,
  snapshot,
  type SocioOffline,
  sincronizar,
  subscreverOffline,
} from "@/lib/offline";

import { Icon } from "../Icon";

type BarcodeDetectorLike = { detect: (v: HTMLVideoElement) => Promise<{ rawValue: string }[]> };

function detectorQR() {
  return (window as unknown as { BarcodeDetector?: new (o: object) => BarcodeDetectorLike }).BarcodeDetector;
}

function subscreverRede(cb: () => void) {
  window.addEventListener("online", cb);
  window.addEventListener("offline", cb);
  return () => {
    window.removeEventListener("online", cb);
    window.removeEventListener("offline", cb);
  };
}

function sinal(ok: boolean) {
  try {
    const ctx = new AudioContext();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.frequency.value = ok ? 880 : 220;
    g.gain.value = 0.08;
    o.connect(g).connect(ctx.destination);
    o.start();
    o.stop(ctx.currentTime + (ok ? 0.12 : 0.35));
  } catch {
    /* sem som */
  }
}

/** Ecrã da receção: leitor QR (USB/Bluetooth ou câmara), pesquisa manual e modo offline. */
export function EcraCheckIn() {
  const online = useSyncExternalStore(subscreverRede, () => navigator.onLine, () => true);
  const [resultado, setResultado] = useState<ResultadoEntrada | null>(null);
  const [texto, setTexto] = useState("");
  const [sugestoes, setSugestoes] = useState<SocioOffline[]>([]);
  const pendentes = useSyncExternalStore(subscreverOffline, () => fila().length, () => 0);
  const snapshotEm = useSyncExternalStore(subscreverOffline, () => snapshot()?.gerado_em ?? null, () => null);
  const [camara, setCamara] = useState(false);
  const [sessao, setSessao] = useState<(ResultadoEntrada & { quando: string })[]>([]);
  const entrada = useRef<HTMLInputElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const ocupado = useRef(false);
  const { dados: hoje, recarregar } = useGestao<CheckIn[]>("checkins");

  const sincronizarTudo = useCallback(async () => {
    if (!navigator.onLine) return;
    const n = await sincronizar();
    await atualizarSnapshot();
    if (n) recarregar();
  }, [recarregar]);

  // Lista offline e fila: atualiza ao abrir, a cada minuto e quando a rede volta.
  useEffect(() => {
    sincronizarTudo();
    const t = setInterval(sincronizarTudo, 60_000);
    window.addEventListener("online", sincronizarTudo);
    return () => {
      clearInterval(t);
      window.removeEventListener("online", sincronizarTudo);
    };
  }, [sincronizarTudo]);

  // O resultado desaparece sozinho para a próxima pessoa.
  useEffect(() => {
    if (!resultado) return;
    const t = setTimeout(() => setResultado(null), 6000);
    return () => clearTimeout(t);
  }, [resultado]);

  const registar = useCallback(
    async (alvo: { codigo?: string; socio_id?: number }) => {
      if (ocupado.current) return;
      ocupado.current = true;
      const r = await registarEntrada(alvo);
      ocupado.current = false;
      sinal(r.permitido);
      setResultado(r);
      setSessao((s) => [{ ...r, quando: new Date().toISOString() }, ...s].slice(0, 20));
      setTexto("");
      setSugestoes([]);
      if (!r.offline) recarregar();
      entrada.current?.focus();
    },
    [recarregar],
  );

  // Leitor por câmara (BarcodeDetector: Chrome/Android; noutros browsers usa-se um leitor USB).
  useEffect(() => {
    if (!camara) return;
    let stream: MediaStream | null = null;
    let ativo = true;
    const Detector = detectorQR();
    if (!Detector) return;
    const detector = new Detector({ formats: ["qr_code"] });
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(async (s) => {
        stream = s;
        if (!video.current) return;
        video.current.srcObject = s;
        await video.current.play();
        let ultimo = "";
        while (ativo) {
          const codigos = await detector.detect(video.current).catch(() => []);
          const valor = codigos[0]?.rawValue;
          if (valor && valor !== ultimo) {
            ultimo = valor;
            await registar({ codigo: valor });
            setTimeout(() => (ultimo = ""), 4000);
          }
          await new Promise((r) => setTimeout(r, 250));
        }
      })
      .catch(() => setCamara(false));
    return () => {
      ativo = false;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [camara, registar]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const valor = texto.trim();
    if (!valor) return;
    // Leitores QR escrevem o código (UUID) e carregam Enter; texto curto é uma pesquisa.
    if (/^[0-9a-f-]{36}$/i.test(valor)) registar({ codigo: valor });
    else if (sugestoes[0]) registar({ socio_id: sugestoes[0].id });
  }

  const tipo = resultado ? (resultado.permitido ? (resultado.motivo.includes("atraso") ? "aviso" : "ok") : "erro") : null;
  const lista = hoje ?? [];

  return (
    <>
      <div className="p-head">
        <div>
          <h1>Check-in</h1>
          <p>Passe o cartão no leitor, use a câmara ou procure pelo nome.</p>
        </div>
      </div>

      <div className="checkin">
        <div className="leitor">
          <div className="rede" role="status">
            <span className="rede__estado">
              <span className={`rede__ponto${online ? "" : " rede__ponto--off"}`} />
              {online ? "Online" : "Sem rede — as entradas ficam guardadas"}
            </span>
            <span>
              {pendentes > 0 && <strong>{pendentes} por sincronizar · </strong>}
              Lista offline: {snapshotEm ? hora(snapshotEm) : "a carregar"}
            </span>
            <button className="btn btn--sm btn--ghost" onClick={sincronizarTudo} disabled={!online}>
              <Icon name="atualizar" size={14} /> Sincronizar
            </button>
          </div>

          <form onSubmit={onSubmit} className="leitor__entrada">
            <Icon name="qr" size={20} />
            <input
              ref={entrada}
              className="input"
              value={texto}
              onChange={(e) => {
                setTexto(e.target.value);
                setSugestoes(/^[0-9a-f-]{20,}$/i.test(e.target.value) ? [] : procurarLocal(e.target.value));
              }}
              placeholder="Ler cartão ou escrever nome / nº de sócio"
              aria-label="Código do cartão, nome ou número de sócio"
              autoFocus
              autoComplete="off"
            />
            {sugestoes.length > 0 && (
              <div className="sugestoes" role="listbox">
                {sugestoes.map((s) => (
                  <button key={s.id} type="button" onClick={() => registar({ socio_id: s.id })}>
                    <span className="avatar" style={{ width: 32, height: 32 }}>
                      {s.n}
                    </span>
                    <span className="linha__principal">
                      <strong>{s.nome}</strong>
                      <span>{s.plano ?? "Sem plano"} · até {dataLonga(s.ate)}</span>
                    </span>
                    <Icon name="arrow-right" size={16} />
                  </button>
                ))}
              </div>
            )}
          </form>

          <div className={`resultado${tipo ? ` resultado--${tipo}` : ""}`} aria-live="assertive">
            {resultado ? (
              <>
                <span className="resultado__icone">
                  <Icon name={resultado.permitido ? "check" : "x"} size={36} />
                </span>
                <h2>{resultado.permitido ? "Pode entrar" : "Entrada recusada"}</h2>
                {resultado.socio && (
                  <p style={{ color: "var(--c-fg)", fontSize: "1.125rem", fontWeight: 600 }}>
                    #{resultado.socio.numero} {resultado.socio.nome}
                  </p>
                )}
                <p>
                  {resultado.motivo}
                  {resultado.socio?.valido_ate && ` · válido até ${dataLonga(resultado.socio.valido_ate)}`}
                </p>
                {resultado.offline && <span className="estado estado--aviso">Validado sem rede</span>}
                {resultado.socio && !resultado.permitido && (
                  <Link href={`/gestao/socios/${resultado.socio.id}`} className="btn btn--sm" style={{ marginTop: 8 }}>
                    Abrir ficha e receber
                  </Link>
                )}
              </>
            ) : (
              <>
                <span className="resultado__icone">
                  <Icon name="qr" size={32} />
                </span>
                <h2 style={{ fontSize: "1.5rem" }}>À espera do cartão</h2>
                <p>O resultado aparece aqui.</p>
              </>
            )}
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn btn--ghost btn--sm"
              onClick={() => {
                if (!camara && !detectorQR()) {
                  alert("Este browser não lê QR pela câmara. Use um leitor USB ou o Chrome no Android.");
                  return;
                }
                setCamara((v) => !v);
              }}
            >
              <Icon name="camara" size={16} /> {camara ? "Fechar câmara" : "Usar câmara"}
            </button>
          </div>
          {camara && <video ref={video} className="leitor__video" muted playsInline />}
        </div>

        <section className="bloco">
          <div className="bloco__topo">
            <h2>Entradas de hoje</h2>
            <span className="muted small">{lista.filter((c) => c.permitido).length} entradas</span>
          </div>
          {sessao.some((s) => s.offline) && (
            <ul className="lista">
              {sessao
                .filter((s) => s.offline)
                .map((s, i) => (
                  <li key={i} className="linha">
                    <span className="hora">{hora(s.quando)}</span>
                    <span className="linha__principal">
                      <strong>{s.socio?.nome ?? "Cartão desconhecido"}</strong>
                      <span>Por sincronizar</span>
                    </span>
                    <span className="estado estado--aviso">Offline</span>
                  </li>
                ))}
            </ul>
          )}
          {lista.length === 0 && !sessao.length && <div className="bloco__vazio">Ainda sem entradas hoje.</div>}
          <ul className="lista" style={{ maxHeight: 560, overflowY: "auto" }}>
            {lista.map((c) => (
              <li key={c.id}>
                <Link href={c.socio ? `/gestao/socios/${c.socio.id}` : "#"} className="linha">
                  <span className="hora">{hora(c.momento)}</span>
                  <span className="linha__principal">
                    <strong>{c.socio?.nome ?? "Cartão desconhecido"}</strong>
                    <span>{c.motivo}</span>
                  </span>
                  <span className={`estado ${c.permitido ? "estado--ok" : "estado--erro"}`}>
                    {c.permitido ? "Entrou" : "Recusado"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
