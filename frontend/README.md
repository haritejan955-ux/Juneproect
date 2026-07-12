# Frontend — US Insurance Claim Processing Agent

Next.js (App Router) + TypeScript + Tailwind CSS. See [../docs](../docs) for architecture and
[../README.md](../README.md) for top-level setup.

## Local development

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Screens

| Route | Screen |
|---|---|
| `/submit` | Claim Submission — upload documents, enter query |
| `/processing/[claimId]` | Processing View — live per-agent status over WebSocket |
| `/decision/[claimId]` | Decision Dashboard — badge, coverage table, fraud panel, citations |
| `/dispute/[claimId]` | Dispute Flow — multi-turn chat contesting a decision |
| `/audit/[claimId]` | Audit Trail — full timestamped agent execution log |

## Scripts

- `npm run dev` — start the dev server
- `npm run build` — production build
- `npm run lint` — ESLint
- `npm run typecheck` — `tsc --noEmit`

## Known dependency advisory (deferred)

`npm audit` reports several Next.js advisories that are only fixed on Next 16
(`npm audit fix --force` will offer this). Next 16 changes the App Router page-props API
(`params`/`searchParams` become `Promise`s), which would require rewriting every dynamic route
in this skeleton — not something to do without testing each screen. Most of the flagged
advisories require features this app doesn't use (Image Optimizer `remotePatterns`, i18n
middleware, CSP nonces, Next-proxied WebSocket upgrades — this app's WebSocket connects directly
from the browser to FastAPI, not through Next). Staying on the latest 14.2.x patch and revisiting
the Next 16 migration as its own tracked piece of work is the deliberate choice here, not an
oversight.
