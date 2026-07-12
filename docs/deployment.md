# Production Deployment Guide

This document covers what "production" changes about running this system, independent of which
infrastructure hosts it. For the concrete AWS reference architecture and Infrastructure-as-Code,
see [`docs/aws-deployment.md`](./aws-deployment.md). For what every environment variable does, see
[`docs/environment-variables.md`](./environment-variables.md). This doc is the layer in between:
principles that apply whether you deploy to AWS, another cloud, or a single VM with
`docker compose up -d`.

## 1. The two images are the unit of deployment

`docker/backend.Dockerfile` and `docker/frontend.Dockerfile` build the only two artifacts that
ship to production — there is no separate "production build" process outside Docker. Both:

- run as a non-root user (`appuser` / `node`),
- expose a `HEALTHCHECK` an orchestrator can poll,
- read all configuration from the environment (backend, at runtime) or build args (frontend, at
  build time — see the "build-time vs. runtime" distinction in
  [`docs/environment-variables.md`](./environment-variables.md)).

Build once per release, push to a registry, deploy the same tagged image to every environment.
Never `docker build` directly on a production host — see §5 (CI/CD).

## 2. Secrets

Three variables are secrets (`API_KEYS`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` — see
[`docs/environment-variables.md`](./environment-variables.md) for the full table). In production:

- **Never** as plain environment variables in a task definition, compose file, or shell profile
  that lands in shell history, process listings (`ps eww`), or a container-orchestrator API
  response that isn't itself access-controlled.
- Use your platform's secret store and resolve at process start: AWS Secrets Manager/SSM (see
  `docs/aws-deployment.md`), or the equivalent on another platform (Vault, GCP Secret Manager,
  Docker Swarm secrets). `pydantic-settings` reads these the same way it reads any other env var —
  there's no code-level difference between "plain env var" and "env var populated by the
  orchestrator from a secret store immediately before the container starts."
- `NEXT_PUBLIC_API_KEY` is the one exception worth re-stating: it's generated and distributed like
  a secret (not committed, not guessable, not shared across environments), but once the frontend
  image is built, it is readable by anyone with browser dev tools. This is a documented scope
  tradeoff, not an oversight — see `docs/security-architecture.md` §9. Rotating it means rebuilding
  and redeploying the frontend image, not just restarting a container.
- Rotate `API_KEYS` by adding the new key alongside the old one (`API_KEYS` is a JSON array —
  multiple valid keys are supported simultaneously), redeploying the backend, updating
  `NEXT_PUBLIC_API_KEY` and redeploying the frontend, then removing the old key in a follow-up
  backend deploy. This order avoids a window where a redeployed service is holding a key the other
  side doesn't accept yet.

## 3. Persistent storage is not optional

The backend writes state to three places under `/app/data` inside the container: the SQLite
database (`DATABASE_URL`), the FAISS indices (`VECTOR_INDEX_DIR`), and generated/uploaded files
(`SYNTHETIC_CLAIMS_DIR`, `UPLOAD_STORAGE_DIR`). None of this is disposable — losing it on every
redeploy means losing every claim decision, audit log entry, and dispute thread the system has
ever recorded.

`/app/data` must be a volume, and that volume must survive container replacement:

- `docker-compose.yml` uses the named volume `backend_data` — correct for a single Docker host,
  but tied to that host's local disk. Moving the container to a different host loses the data
  unless the volume itself is backed by shared/networked storage.
- The AWS reference architecture mounts an EFS access point at the same path for exactly this
  reason — see `docs/aws-deployment.md`.

`POLICY_CORPUS_DIR` is the one exception: it's shipped inside the image (the Dockerfile `COPY`s
`backend/data/`) and rebuilt from image content via `scripts/build_policy_index.py`, not runtime
state, so it does not need to be on the persistent volume.

**Back up the volume.** A snapshot of `/app/data` (EFS backup, EBS/volume snapshot, or a scheduled
`sqlite3 .backup` + file copy of the indices) is the only recovery path if the volume is lost or
corrupted — there is no upstream source of truth to rebuild claim history from.

## 4. The single-writer constraint

This system uses SQLite deliberately (`docs/design-decisions.md` decision #3: "single-writer
process, simple schema — Postgres solves a concurrency problem this system doesn't have"). The
production consequence of that choice: **the backend cannot be horizontally scaled to multiple
concurrent instances writing to the same database file.** Run exactly one backend task/container
against a given data volume at a time.

This is a real constraint, stated honestly rather than glossed over:

- Rolling deploys must be replace-one-then-terminate-the-old (or brief downtime), not
  run-N-copies-behind-a-load-balancer. `docs/aws-deployment.md` documents how the ECS service is
  configured for exactly one task and a deployment strategy that respects this.
- Vertical scaling (a larger task/instance) is available if throughput becomes a bottleneck;
  horizontal scaling is not, without first migrating to a networked database — a larger change than
  this deployment guide covers, and not needed at this system's expected claim volume.
- The frontend has no such constraint (it's stateless) and can run multiple replicas behind a load
  balancer freely.

## 5. HTTPS / TLS termination

Neither Dockerfile terminates TLS — both containers serve plain HTTP (`uvicorn` on 8000, Next.js on
3000). This is intentional: TLS termination belongs at the edge (a load balancer or reverse proxy
in front of the containers), not duplicated inside every service instance.

- In the AWS reference architecture, an Application Load Balancer terminates TLS using an ACM
  certificate and forwards plain HTTP to the ECS tasks over the (private, VPC-internal) network —
  see `docs/aws-deployment.md`.
- On a single-VM deployment, put a reverse proxy (nginx, Caddy, Traefik) in front of both
  `docker compose` services for the same reason — don't expose ports 8000/3000 directly to the
  internet.
- Once the backend is behind TLS, `NEXT_PUBLIC_WS_BASE_URL` must be `wss://`, not `ws://` — a
  frontend served over HTTPS making a plain `ws://` connection is mixed content and browsers will
  block it. This is a build-time value (see
  [`docs/environment-variables.md`](./environment-variables.md)), so it has to be correct *before*
  building the frontend image for that environment, not patched in afterward.
- `CORS_ORIGINS` must list the frontend's real `https://` origin in every non-local environment.
  This is the single most common first-deploy misconfiguration: get it wrong and every browser
  request fails CORS preflight while `curl` against the same endpoint works fine, which is a
  confusing failure mode to debug blind — check this first if a fresh deployment's frontend can't
  reach its backend.

## 6. CI/CD pipeline overview

Two separate GitHub Actions workflows, split by responsibility:

- **`.github/workflows/ci.yml`** — runs on every push to `main` and every pull request. Lints,
  type-checks, and tests both backend (`ruff`, `mypy`, `pytest`) and frontend (`tsc`, `eslint`,
  `vitest`, `next build`). This is a merge gate, not a deploy step — it never touches AWS or builds
  a Docker image.
- **`.github/workflows/deploy.yml`** — runs on push to `main` after CI passes (or manually via
  `workflow_dispatch`). Builds both Docker images, pushes them to ECR, and updates the ECS
  services to the new image tag. Authenticates to AWS via GitHub OIDC (no long-lived AWS access
  keys stored as repository secrets) — see `docs/aws-deployment.md` for the full workflow and the
  IAM role trust policy it depends on.

The split matters: CI answers "is this change correct," deploy answers "should this change go
live." Keeping them separate means a docs-only PR or a feature branch never triggers an AWS
deployment, and a deploy can be re-run (e.g., to roll back to a previous image tag) without
re-running the full test suite.

**Rollback:** because every deploy is "point the service at image tag X," rolling back is
re-deploying the previous known-good tag — either by re-running `deploy.yml` with
`workflow_dispatch` against an older commit, or (fastest, no rebuild) updating the ECS service to
the previous image URI directly, as described in `docs/aws-deployment.md`.

## 7. Health checks and zero-downtime deploys

Both images ship a `HEALTHCHECK` (backend polls `/health`; frontend polls `/`). `docker-compose.yml`
uses this for local orchestration (`depends_on: condition: service_healthy` — the frontend won't
start serving traffic checks until the backend reports healthy). The AWS ECS service uses the same
endpoint as its ALB target group health check, so a new task is only registered to receive traffic
once it's actually ready — see `docs/aws-deployment.md`. Given the single-writer constraint (§4),
the backend's deploy is replace-then-drain rather than N-at-once, but the health check still gates
when the *new* task starts receiving traffic, avoiding a window where requests hit a container
that hasn't finished starting up.

## 8. Logging and observability

Both containers log to stdout/stderr (`PYTHONUNBUFFERED=1` on the backend; Next.js does this by
default) — deliberately, so the platform's log collector is the single place logs end up, rather
than each container managing its own log files. In the AWS reference architecture this is
CloudWatch Logs via the `awslogs` driver, configured per-container in the ECS task definition (see
`docs/aws-deployment.md`). `LOG_LEVEL` controls verbosity (see
[`docs/environment-variables.md`](./environment-variables.md)); the audit log
(`docs/security-architecture.md` §8) is separate from application logs — it's an append-only table
in the same SQLite database as claim decisions, not a log stream, and is covered by the same volume
backup requirement in §3.

## 9. Minimal non-AWS production path

If you don't need the AWS architecture, the same two images run in production on any single Docker
host with:

```bash
git clone <repo> && cd Juneproect
cp .env.example .env   # fill in real secrets, generate real API_KEYS
docker compose -f docker-compose.yml up -d --build
```

plus a reverse proxy in front for TLS (§5) and a backup job for the `backend_data` volume (§3).
This is a valid production deployment for a low-traffic or internal-only instance — it just
inherits that single host's availability (no failover) and doesn't get the ALB/ECS
rolling-deploy behavior of §7. `docs/aws-deployment.md` is the path to take once those matter.
