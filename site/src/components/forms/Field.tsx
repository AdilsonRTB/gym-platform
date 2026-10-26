import Link from "next/link";
import type { ReactNode } from "react";

export function Field({
  id,
  label,
  erro,
  opcional,
  children,
}: {
  id: string;
  label: string;
  erro?: string;
  opcional?: boolean;
  children: ReactNode;
}) {
  return (
    <div className={`field${erro ? " field--erro" : ""}`}>
      <label htmlFor={id}>
        {label} {opcional && <span className="opcional">(opcional)</span>}
      </label>
      {children}
      {erro && (
        <p className="erro" id={`${id}-erro`} role="alert">
          {erro}
        </p>
      )}
    </div>
  );
}

export function Consentimento({ texto, erro }: { texto: string; erro?: string }) {
  return (
    <div>
      <label className="check">
        <input type="checkbox" name="consentimento" required aria-invalid={Boolean(erro)} />
        <span>
          {texto}{" "}
          <Link href="/privacidade" target="_blank">
            Política de privacidade
          </Link>
          .
        </span>
      </label>
      {erro && (
        <p className="erro" role="alert" style={{ marginTop: 8 }}>
          {erro}
        </p>
      )}
    </div>
  );
}

/** Campo escondido para apanhar bots (os humanos não o veem). */
export function Honeypot() {
  return (
    <div className="hp" aria-hidden="true">
      <label>
        Website
        <input type="text" name="website" tabIndex={-1} autoComplete="off" />
      </label>
    </div>
  );
}

export function Sucesso({ titulo, texto }: { titulo: string; texto: string }) {
  return (
    <div className="notice" role="status">
      <span className="notice__icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M20 6 9 17l-5-5" />
        </svg>
      </span>
      <div>
        <strong>{titulo}</strong>
        <p className="muted" style={{ margin: "4px 0 0" }}>
          {texto}
        </p>
      </div>
    </div>
  );
}
