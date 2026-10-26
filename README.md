# Plataforma White Label para Ginásios

Cada ginásio tem o seu site, a sua marca e o seu domínio, servidos pela mesma plataforma.
O plano completo está em [roadmap-plataforma-ginasios.md](roadmap-plataforma-ginasios.md).

| Pasta | O que é |
| --- | --- |
| [backend/](backend/) | Django 5.2 + Wagtail 7.0 (LTS): Admin CMS, API REST, multi-tenancy, pagamentos e faturação |
| [site/](site/) | Next.js 16 (App Router, TypeScript): um único site que serve todos os ginásios pelo domínio |
| [infra/](infra/) | Caddy com TLS on-demand (SSL automático para domínios próprios) |
| [docker-compose.yml](docker-compose.yml) | PostgreSQL, Redis, backend, site e Caddy |

## Arranque rápido (local)

Requisitos: Python 3.12 e Node 20.

```bash
# 1. Backend (Admin + API) → http://localhost:8000/admin/
cd backend
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo          # 3 ginásios de demonstração, um por modelo de site
.venv/bin/python manage.py runserver 8000

# 2. Site → http://forca.localhost:3100
cd site
cp .env.example .env.local
npm install
npm run dev
```

Sites de demonstração (o Chrome e o Firefox resolvem `*.localhost` sozinhos):

| Ginásio | Modelo | Endereço |
| --- | --- | --- |
| Força Praia | Essencial (claro, sóbrio) | http://forca.localhost:3100 |
| Mindelo Fit Studio | Atelier (suave, editorial) | http://mindelo.localhost:3100 |
| Sal Energy Club | Energia (escuro, intenso) | http://sal.localhost:3100 |

Contas de demonstração no Admin (`http://localhost:8000/admin/`):

| Conta | Palavra-passe | Perfil |
| --- | --- | --- |
| `admin` | `admin` | Equipa da plataforma (superutilizador) |
| `dono@forca.cv` | `demo12345` | Dono do Força Praia |
| `gestor@forca.cv` | `demo12345` | Gestor do Força Praia |
| `rececao@forca.cv` | `demo12345` | Rececionista do Força Praia |
| `treinador@forca.cv` | `demo12345` | Treinador do Força Praia (ligado ao perfil de Carla Semedo) |

(O mesmo padrão existe para `mindelo` e `sal`.) Cada ginásio de demonstração tem 36 sócios com assinaturas
em vários estados (em dia, a renovar, em atraso, suspenso) e entradas dos últimos 14 dias.

### Gestão do ginásio (fase 2)

| Área | Endereço | Quem |
| --- | --- | --- |
| Painel da receção | http://forca.localhost:3100/gestao | Equipa (as mesmas contas do Admin) |
| App do sócio | http://forca.localhost:3100/app | Sócios, com código enviado por WhatsApp/SMS/email |

Em desenvolvimento, os códigos de acesso da app e os lembretes não são enviados: aparecem no terminal do Django
(`[whatsapp:simulado] …`). Os pagamentos e a faturação dos ginásios de demonstração
usam os fornecedores **simulados**: a adesão em `/aderir` abre uma página de pagamento de teste e a fatura
é "emitida" sem contactar a SISP nem a DNRE.

### Com Docker

```bash
docker compose up --build
docker compose exec backend python manage.py seed_demo
```

Em produção: `docker compose --profile producao up -d` com `ADMIN_DOMAIN`, `ACME_EMAIL`, `DJANGO_DEBUG=false`,
`DJANGO_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `SITE_PUBLIC_SCHEME=https`, `SITE_PUBLIC_PORT=` (vazio) e
`API_PUBLIC_URL=https://<ADMIN_DOMAIN>` definidos num `.env`. Ver [backend/.env.example](backend/.env.example).

## Como funciona

```
visitante → forca.cv/planos → Caddy (SSL) → Next.js
  proxy.ts: domínio → rota interna /forca.cv/planos
  fetch à API com X-Gym-Host: forca.cv  (em cache, com tags por ginásio)
      → Django: TenantMiddleware resolve o ginásio pelo domínio
      → managers filtram todo o conteúdo pelo ginásio atual
Wagtail "Publicar" → webhook /api/revalidate → só as tags desse ginásio são revalidadas
```

**Isolamento entre ginásios** (o maior risco do roadmap):

- Todo o conteúdo herda de `TenantModel` ([backend/apps/tenants/models.py](backend/apps/tenants/models.py)):
  chave `ginasio` + manager que filtra sempre pelo ginásio do pedido (`ContextVar`).
- Pedidos sem ginásio resolvido não veem nada; criar conteúdo sem ginásio falha.
- Formulários do Admin e da API recalculam as escolhas (ex.: modalidade de uma aula) no pedido, com o filtro
  do ginásio ([backend/apps/tenants/forms.py](backend/apps/tenants/forms.py)).
- Páginas e media usam as permissões nativas do Wagtail sobre a árvore e a coleção de cada ginásio.
- Testes obrigatórios em [backend/tests/test_isolamento.py](backend/tests/test_isolamento.py).

**Perfis** (grupos criados por ginásio ao provisionar):

| Perfil | Acesso |
| --- | --- |
| Dono | Tudo, incluindo marca, pagamentos, faturação e equipa |
| Gestor | Conteúdo, páginas, horário, planos, marca e leads; sem configurações fiscais |
| Rececionista | Leads, horário e registo de pagamentos presenciais |
| Treinador | Só o próprio perfil e as suas aulas (em rascunho, para aprovação) |

**Gestão de sócios** ([backend/apps/gestao/](backend/apps/gestao/)):

- **Sócios** com número sequencial por ginásio e código QR (o cartão). "Cartão perdido" gera um código novo.
- **Assinaturas e cobranças:** cada pagamento avança a validade da assinatura. A tarefa `gestao_diaria` cria a
  cobrança do período seguinte (7 dias antes, configurável) e envia lembretes antes do vencimento e com 1 e 7
  dias de atraso, sem repetir.
- **Pagamentos presenciais** (numerário, TPA, transferência) no painel, com fatura automática. **Online** na app,
  pelo mesmo fornecedor da adesão (SISP quando estiver configurada). Uma adesão paga no site cria o sócio.
- **Check-in tolerante a falhas de rede:** o painel guarda no dispositivo uma lista mínima de sócios e, sem rede,
  valida a entrada localmente e guarda-a numa fila. Quando a rede volta, a fila é enviada; o servidor ignora
  duplicados (`client_id`). Funciona com leitores QR USB/Bluetooth (modo teclado), com a câmara (Chrome/Android)
  e com pesquisa por nome ou número.
- **App do sócio** (PWA instalável com a marca do ginásio): cartão QR, validade, mensalidades por pagar, histórico
  de pagamentos e faturas, treinos do mês. Entrada sem palavra-passe, com código de 6 dígitos (10 min, 5 tentativas).
- **Sessões:** tokens assinados com o id do ginásio, guardados em cookies httpOnly pelo Next.js; um token de um
  ginásio é recusado noutro. Regras de tolerância e lembretes em *Configurações → Gestão de sócios*.

**Contrato Admin ↔ Site:** cada bloco do StreamField ([backend/apps/content/blocks.py](backend/apps/content/blocks.py))
tem o componente correspondente em [site/src/components/blocks/Blocks.tsx](site/src/components/blocks/Blocks.tsx).

## Estado face ao roadmap

| Sprint | Estado | Notas |
| --- | --- | --- |
| S1 Arranque | ✅ | Docker Compose, Django + Wagtail + DRF, Next.js, CI (lint, testes, build) |
| S2 Multi-tenancy | ✅ | Managers, middleware por domínio, perfis, auditoria (log do Wagtail + ações próprias), Caddy on-demand, testes de isolamento |
| S3 Marca e início | ✅ | Configuração da marca por site, S3 opcional, StreamField, cabeçalho/rodapé, renderizador de blocos |
| S4 Conteúdo | ✅ | Modalidades, Treinadores, Planos (CVE), Testemunhos, FAQ + páginas e API |
| S5 Horário e publicação | ✅ | Aulas, rascunho/publicado em snippets e páginas, pré-visualização headless por token, revalidação por tags |
| S6 SEO e modelos | ✅ | SEO por página e por site, redirecionamentos, sitemap/robots por domínio, 3 modelos, JSON-LD, analítica |
| S7 Leads e privacidade | ✅ | Caixa de leads, email + WhatsApp, consentimento registado, exportar/eliminar dados, aviso de cookies |
| S8 Adesão e pagamento | 🟡 | Fluxo completo com fornecedor simulado. **SISP:** fingerprints implementados, validar com credenciais de teste. **e-Fatura:** esqueleto do XML/transmissão, a substituir pelo cliente que a equipa já tem |
| Fase 2 · MVP de gestão | ✅ | Sócios, assinaturas, cobranças recorrentes, pagamentos presenciais com fatura, check-in QR offline, lembretes WhatsApp/SMS/email, app do sócio |
| S9–S10 Piloto | ⏳ | Operacional: onboarding, domínio do piloto, Sentry (já suportado por `SENTRY_DSN`), formação, backups |

### Antes de produção

- Validar o Vinti4Net com as credenciais de teste da SISP ([backend/apps/billing/providers/sisp.py](backend/apps/billing/providers/sisp.py)).
- Integrar o cliente e-Fatura existente em [backend/apps/billing/providers/efatura_cv.py](backend/apps/billing/providers/efatura_cv.py).
- Gerar `FIELD_ENCRYPTION_KEY` e guardá-la em local seguro (sem ela não é possível ler as credenciais cifradas).
- Configurar `PLATFORM_IPS` para a verificação de DNS de domínios próprios no Admin.
- Configurar o envio real de WhatsApp (`WHATSAPP_API_*`) e SMS (`SMS_API_*`); sem isso os códigos da app só
  chegam por email.
- Correr `python manage.py sincronizar_permissoes` depois de migrações que acrescentem modelos (atualiza os perfis).

## Testes e qualidade

```bash
cd backend && .venv/bin/pytest && .venv/bin/ruff check .
cd site && npm run lint && npm run typecheck && npm run build
```
