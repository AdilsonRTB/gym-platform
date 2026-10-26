"use client";

import Link from "next/link";
import Script from "next/script";
import { useState, useSyncExternalStore } from "react";

const CHAVE = "consentimento-cookies";
const subscribe = () => () => {};

function ler(): "sim" | "nao" | null {
  try {
    return localStorage.getItem(CHAVE) as "sim" | "nao" | null;
  } catch {
    return null;
  }
}

/**
 * Só aparece quando o ginásio usa analítica com cookies (Google Analytics).
 * O GA só é carregado depois de o visitante aceitar (CNPD).
 */
export function CookieBanner({ ga4Id }: { ga4Id: string }) {
  // `undefined` no servidor: o aviso só aparece no browser, depois de ler a escolha guardada.
  const guardada = useSyncExternalStore(subscribe, ler, () => undefined);
  const [nova, setEscolha] = useState<"sim" | "nao">();
  const escolha = nova ?? guardada;

  function guardar(valor: "sim" | "nao") {
    try {
      localStorage.setItem(CHAVE, valor);
    } catch {
      /* navegação privada: a escolha vale só para esta visita */
    }
    setEscolha(valor);
  }

  return (
    <>
      {escolha === "sim" && (
        <>
          <Script src={`https://www.googletagmanager.com/gtag/js?id=${ga4Id}`} strategy="afterInteractive" />
          <Script id="ga4" strategy="afterInteractive">
            {`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','${ga4Id}',{anonymize_ip:true});`}
          </Script>
        </>
      )}
      {escolha === null && (
        <div className="cookie-banner" role="dialog" aria-label="Cookies">
          <p>
            Usamos cookies de analítica para melhorar o site, só com a sua autorização.{" "}
            <Link href="/privacidade">Saber mais</Link>
          </p>
          <div className="cookie-banner__acoes">
            <button className="btn btn--sm" onClick={() => guardar("sim")}>
              Aceitar
            </button>
            <button className="btn btn--sm btn--ghost" onClick={() => guardar("nao")}>
              Recusar
            </button>
          </div>
        </div>
      )}
    </>
  );
}
