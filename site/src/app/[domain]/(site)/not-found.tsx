import Link from "next/link";

export default function NotFound() {
  return (
    <section className="container not-found">
      <p className="display">404</p>
      <h1 className="h2">Página não encontrada</h1>
      <p className="lead" style={{ marginInline: "auto" }}>
        A página que procura mudou de lugar ou já não existe.
      </p>
      <div>
        <Link href="/" className="btn">
          Voltar ao início
        </Link>
      </div>
    </section>
  );
}
