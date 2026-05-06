# Lab 17 - Cloudflare Workers Edge Deployment

This document covers the full Lab 17 checklist for a Workers-based API.

Command evidence is stored in `temp.txt`.

## 1) Deployment summary

- Worker name: `lab17-edge-api`
- Project path: `edge-api/`
- Main routes:
  - `/`
  - `/health`
  - `/edge`
  - `/counter`
  - `/config`
- Public URL:
  - `https://lab17-edge-api.ilyhalab.workers.dev`

## 2) Setup and platform concepts (Task 1)

- Cloudflare account and Wrangler authentication:
  - confirmed by `wrangler whoami` output in `temp.txt`
  - account id: `[REDACTED_ACCOUNT_ID]`
- `workers.dev` subdomain was registered:
  - `ilyhalab.workers.dev`
- `wrangler.jsonc` role:
  - declares Worker name, entry point, compatibility date
  - defines plaintext `vars`
  - defines KV binding (`SETTINGS`)

## 3) Worker API implementation and deployment (Task 2)

Implemented routes:
- `/health` -> health JSON
- `/` -> metadata and endpoint list
- `/edge` -> edge request metadata
- `/counter` -> persisted KV counter
- `/config` -> config/secrets-presence check

Deployment evidence:
- successful deploy output in `temp.txt`
- deployed URL and version id recorded:
  - `d9ca0c33-7627-4a99-bae4-ec591b688a6b`

## 4) Global edge behavior and routing concepts (Task 3)

### Edge metadata verification

`/edge` response includes:
- `colo` (`AMS`)
- `country` (`NL`)
- `city`
- `asn`
- `httpProtocol`
- `tlsVersion`

This confirms request metadata is provided at Cloudflare edge runtime.

### Global distribution explanation

Cloudflare Workers automatically executes near the user across Cloudflare POPs.  
Unlike VM/PaaS multi-region setups, there is no manual "deploy to N regions" workflow for baseline global execution.

### Routing concepts

- `workers.dev`: quickest public hostname for Worker deployments.
- Routes: attach Worker to traffic on an existing Cloudflare-managed zone/path.
- Custom Domains: make the Worker serve your own domain/subdomain directly.

## 5) Config, secrets, and KV persistence (Task 4)

### Plaintext vars

Configured in `wrangler.jsonc`:
- `APP_NAME`
- `COURSE_NAME`

Plaintext vars are not secrets because they are part of deploy configuration and must not hold sensitive values.

### Secrets

Set through Wrangler:
- `API_TOKEN`
- `ADMIN_EMAIL`

Verified by `/config` response:
- `"apiToken": true`
- `"adminEmail": true`

### Workers KV

- binding: `SETTINGS`
- namespace id: `489251d1d3714fc58da940269c9c7ea3`

Persistence verification:
- first `/counter` call -> `visits: 1`
- second `/counter` call -> `visits: 2`
- after redeploy, state remains in the same KV namespace (persistent storage independent of Worker version).

## 6) Observability and operations (Task 5)

### Logs

- `console.log(...)` added in Worker request path
- `wrangler tail` used; live request log evidence captured

### Metrics

- Worker dashboard/URL behavior reviewed as runtime verification source
- request/response behavior validated through public endpoint invocations

### Deployment history and rollback readiness

- `wrangler deployments list` output captured in `temp.txt`
- multiple versions recorded, including secret-change and deploy versions
- rollback can be executed with `wrangler rollback` if needed.

## 7) Evidence references

- Terminal evidence file:
  - `temp.txt`
- Screenshots:
  - `screenshots/lab17_worker_subdomain.png`
  - `screenshots/lab17_working_query_to worker.png`

## 8) Kubernetes vs Cloudflare Workers comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | Higher (cluster, manifests, networking, storage) | Lower (project + wrangler deploy) |
| Deployment speed | Slower (image build/push, rollout) | Very fast edge publish |
| Global distribution | Requires multi-region cluster strategy | Built-in global edge routing |
| Cost (for small apps) | Often higher due to baseline infra | Often lower pay-as-you-go |
| State/persistence model | PV/PVC + external DB/cache | KV/D1/R2 bindings, edge-native primitives |
| Control/flexibility | Maximum control, any container workload | More constrained runtime model |
| Best use case | Complex stateful platforms/microservices | Lightweight global APIs, edge logic |

## 9) When to use each

- Prefer Kubernetes when:
  - full runtime/network/storage control is required
  - complex stateful or long-running services are needed
  - advanced custom platform integrations are required
- Prefer Workers when:
  - globally distributed API/edge logic is the main goal
  - minimal ops overhead and fast iteration are priorities
  - request-driven workloads fit edge runtime constraints
- Recommendation:
  - Workers for edge/API front layers and globally distributed lightweight services.
  - Kubernetes for heavy backend/stateful platform workloads.

## 10) Reflection

- Easier than Kubernetes:
  - faster setup and deploy cycle
  - instant public endpoint with `workers.dev`
- More constrained:
  - runtime model and platform-specific bindings
- What changed because Workers is not a Docker host:
  - no container daemon/process orchestration model
  - code executes in request-driven edge runtime instead of containerized service host

## 11) Original Lab 17 checklist status

- [x] Cloudflare account created
- [x] Workers project initialized
- [x] Wrangler authenticated
- [x] Worker deployed to `workers.dev`
- [x] `/health` endpoint working
- [x] Edge metadata endpoint implemented
- [x] At least 1 plaintext variable configured
- [x] At least 2 secrets configured
- [x] KV namespace created and bound
- [x] Persistence verified after redeploy
- [x] Logs or metrics reviewed
- [x] Deployment history viewed
- [x] `WORKERS.md` documentation complete
- [x] Kubernetes comparison documented

