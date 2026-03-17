# Lab 8 — Metrics & Monitoring with Prometheus

## Architecture

```
+------------------+        /metrics        +--------------+        PromQL        +-------------+
| App (Flask)      |  --------------------> | Prometheus   |  --------------- -> | Grafana     |
| devops-info svc  |                        | (scraper)    |                    | dashboards  |
+------------------+                        +--------------+                    +-------------+
         |                                           |
         | logs (Lab 7)                              | scrape /metrics
         v                                           v
      Promtail  ------------------------------->     Loki
```

## Application Instrumentation

Implemented in `labs_solution/lab1/app_python/app.py` with `prometheus-client`:

- `http_requests_total{method,endpoint,status_code}` (Counter)
  - Request rate + error rate (RED: Rate, Errors)
- `http_request_duration_seconds{method,endpoint}` (Histogram)
  - Latency distribution (RED: Duration)
- `http_requests_in_progress` (Gauge)
  - Current concurrent requests
- `devops_info_endpoint_calls{endpoint}` (Counter)
  - Business usage per endpoint
- `devops_info_system_collection_seconds` (Histogram)
  - System info collection time

Rationale: RED method coverage + lightweight business metrics without high-cardinality labels.

## Prometheus Configuration

File: `labs_solution/lab8/prometheus/prometheus.yml`

- `scrape_interval`: 15s
- `evaluation_interval`: 15s
- Retention is enforced by Prometheus flags in `labs_solution/lab8/docker-compose.yml`:
  - `--storage.tsdb.retention.time=15d`
  - `--storage.tsdb.retention.size=10GB`

Scrape targets:
- `prometheus` -> `localhost:9090`
- `app` -> `app-python:8080/metrics`
- `loki` -> `loki:3100/metrics`
- `grafana` -> `grafana:3000/metrics`

## Dashboard Walkthrough

Custom panels (Grafana):
- Request Rate: `sum(rate(http_requests_total[5m])) by (endpoint)`
- Error Rate: `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
- p95 Latency: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- Latency Heatmap: `rate(http_request_duration_seconds_bucket[5m])`
- Active Requests: `http_requests_in_progress`
- Status Code Distribution: `sum by (status_code) (rate(http_requests_total[5m]))`
- Uptime: `up{job="app"}`

Exported dashboard JSON:
- `labs_solution/lab8/docs/evidence/lab8_dashboard.json`

## PromQL Examples

1. `sum(rate(http_requests_total[5m])) by (endpoint)` — request rate per endpoint
2. `sum(rate(http_requests_total{status_code=~"5.."}[5m]))` — error rate (5xx)
3. `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` — p95 latency
4. `rate(http_request_duration_seconds_bucket[5m])` — latency distribution
5. `http_requests_in_progress` — active concurrent requests
6. `up{job="app"}` — service up/down

RED evidence screenshots:
- Rate: `labs_solution/lab8/docs/evidence/lab8_promtail_rate.png`
- Errors: `labs_solution/lab8/docs/evidence/lab8_promtail_error.png`
- Duration: `labs_solution/lab8/docs/evidence/lab8_promtail_duration.png`

## Production Setup

- Health checks configured for Loki, Grafana, Prometheus, App in `labs_solution/lab8/docker-compose.yml`.
- Resource limits:
  - Prometheus: 1G / 1 CPU
  - Loki: 1G / 1 CPU
  - Grafana: 512M / 0.5 CPU
  - App: 256M / 0.5 CPU
  - Promtail: 256M / 0.5 CPU
- Retention:
  - Prometheus flags: `--storage.tsdb.retention.time=15d`, `--storage.tsdb.retention.size=10GB`
- Persistence:
  - Volumes: `prometheus-data`, `loki-data`, `grafana-data`

## Testing Results

Screenshots and artifacts:
- `/metrics` output: `labs_solution/lab8/docs/evidence/lab8_metrics_endpoint.png`
- Prometheus targets UP: `labs_solution/lab8/docs/evidence/lab_8_prom_up.png`
- PromQL query success: `labs_solution/lab8/docs/evidence/lab_8_prom_query.png`
- Dashboard (live data + 6+ panels): `labs_solution/lab8/docs/evidence/lab8_dashboard_custom.png`
- Retention + persistence after restart: `labs_solution/lab8/docs/evidence/lab8_retention_after_restart.png`

## Challenges & Solutions

- Prometheus failed to start because `retention_time` and `retention_size` were placed in the config file.
  - Fix: remove those fields from `prometheus.yml` and set retention via command flags in compose.
- Promtail healthcheck failed because the image lacks `wget/curl`.
  - Fix: remove the promtail healthcheck to avoid false unhealthy status.

## Metrics vs Logs (Lab 7)

- Logs: event details and context for debugging.
- Metrics: trends and performance for alerting/dashboards.
- Together: metrics show what changed; logs explain why.
