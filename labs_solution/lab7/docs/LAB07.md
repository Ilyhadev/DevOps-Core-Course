# Lab 07 - Observability & Logging with Loki Stack

**Loki Version:** 3.0.0 (TSDB storage)  
**Promtail Version:** 3.0.0  
**Grafana Version:** 12.3.1  
**Stack Type:** Docker Compose (single-node)

---

## 1. Architecture Overview

### Centralized Logging Architecture

This lab implements a production-ready centralized logging solution using Grafana Loki stack, which provides an efficient alternative to Elasticsearch-based approaches.

**Key Components:**

1. **Loki (Port 3100):** Log storage and query engine
   - Uses TSDB (Time Series Database) index type for 10x faster queries
   - Filesystem backend for data persistence
   - Supports LogQL query language for sophisticated log filtering

2. **Promtail (Port 9080):** Log collector and forwarder
   - Discovers containers via Docker socket (`/var/run/docker.sock`)
   - Extracts labels from container metadata and labels
   - Pushes logs to Loki via HTTP API

3. **Grafana (Port 3000):** Visualization and dashboarding
   - Connects to Loki data source
   - Provides UI for LogQL queries (Explore view)
   - Interactive dashboards with multiple panel types

4. **Application (Port 8000):** Python Flask service
   - Generates structured JSON logs
   - Integrated into Docker logging network
   - Automatically discovered by Promtail

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Host                                │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │   Loki   │  │Promtail  │  │ Grafana  │  │  app-python  │ │
│  │ :3100    │  │ :9080    │  │ :3000    │  │ :8000        │ │
│  └────┬─────┘  └────┬─────┘  └─────┬────┘  └──────┬───────┘ │
│       │             │              │              │         │
│       │             │              │              │         │
│       │ HTTP API    │stdout/stderr │ HTTP         │         │
│       │ /push       │              │ requests     │         │
│       │             │              │              │         │
│       └─────────────┴─────────────┴───────────────┘         │
│                    logging network                          │
│                  (bridge driver)                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────────┤
│  │  /var/run/docker.sock (mounted RO)                       │
│  │  /var/lib/docker/containers/* (mounted RO)               │
│  └──────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

### Why Loki Instead of Elasticsearch?

| Aspect | Loki | Elasticsearch |
|--------|------|----------------|
| Memory Usage | Low (~200MB) | High (~1GB+) |
| Query Speed | Fast (TSDB index) | Slower indexing |
| Index Size | Small | Large |
| Setup Complexity | Simple | Complex |
| Label-based | Yes |  No |
| LogQL | Simple |  Lucene/ES DSL |

---

## 2. Deployment & Configuration

### Project Structure

```
lab7/
├── monitoring/
│   ├── docker-compose.yml          # Stack orchestration
│   ├── loki/
│   │   └── config.yml              # Loki configuration (TSDB + 7-day retention)
│   ├── promtail/
│   │   └── config.yml              # Promtail Docker discovery + relabeling
│   └── data/                       # Runtime (volumes mounted here)
└── docs/
    ├── LAB07.md                    # This documentation
    └── screenshots_evidence/       # Evidence screenshots
        ├── docker_ps.png           # All services healthy
        ├── graphana_login.png      # Login page (auth enabled)
        ├── graphana_3_containers.png
        ├── graphana_raw_logs_pyapp.png
        ├── python_json_logs.png
        ├── filtered_logs_pyapp.png
        ├── rate_logs_pyapp.png
        └── graphana_dashboard.png
```

### Deployment Steps

#### Step 1: Clone/Create Project Structure

```bash
cd /labs_solution/lab7
mkdir -p monitoring/{loki,promtail}
cd monitoring
```

#### Step 2: Deploy Stack

```bash
# Using Docker Compose v2 CLI (note: space, not hyphen)
docker compose up -d

# Verify services are running
docker compose ps
```

**Expected Output:**
```
NAME         IMAGE                    STATUS
app-python   devops-info-service      Up (healthy)
grafana      grafana/grafana:12.3.1   Up (healthy)
loki         grafana/loki:3.0.0       Up (healthy)
promtail     grafana/promtail:3.0.0   Up
```

#### Step 3: Verify Connectivity

```bash
# Test Loki readiness
curl http://localhost:3100/ready
# Expected: "ready"

# Check Promtail is running and collecting logs
docker compose logs promtail | head -20
# Look for: "discovered 4 targets" or similar container discovery messages

# Access Grafana
open http://localhost:3000
# Login with admin / admin
```

#### Step 4: Configure Grafana Data Source

1. Navigate to **Connections** -> **Data sources**
2. Click **Add data source**
3. Select **Loki**
4. Set URL: `http://loki:3100`
5. Click **Save & Test** (should show "Data source is working")

#### Step 5: Verify Logs Flow

In Grafana **Explore** tab:
- Select **Loki** data source
- Query: `{job="docker"}`
- Click **Run query** (should show logs from 4+ containers)

---

## 3. Configuration Details

### Loki Configuration (`loki/config.yml`)

**Key Design Decisions:**

```yaml
# Authentication disabled for development
auth_enabled: false

# Server configuration
server:
  http_listen_port: 3100
  log_level: info

# Common configuration (Loki 3.0 simplified)
common:
  instance_addr: localhost
  path_prefix: /loki
  storage:
    filesystem:                    # Local storage (not S3/GCS)
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1            # Single node = 1
  ring:
    kvstore:
      store: inmemory             # No distributed state needed

# Schema configuration (TSDB index type)
schema_config:
  configs:
    - from: 2026-01-01
      store: tsdb                  # 10x faster than boltdb-shipper
      object_store: filesystem
      schema: v13                  # Latest TSDB schema
      index:
        prefix: index_
        period: 24h               # Rotation every 24 hours

# Retention policy: 7 days (504 hours)
limits_config:
  retention_period: 168h

# Automatic cleanup of old logs
compactor:
  working_directory: /loki
  compaction_interval: 10m
  retention_enabled: true
  delete_request_store: filesystem
```

**Why TSDB?**
- Introduced in Loki 3.0 as default index type
- 10x faster queries compared to boltdb-shipper
- Lower memory footprint
- Better compression

### Promtail Configuration (`promtail/config.yml`)

**Key Design Decisions:**

```yaml
# Promtail's own server (internal use)
server:
  http_listen_port: 9080
  log_level: debug

# Track log read position
positions:
  filename: /tmp/positions.yaml    # Persists read position

# Send logs to Loki
clients:
  - url: http://loki:3100/loki/api/v1/push

# Docker service discovery
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s        # Detect new containers every 5s
    
    # Label extraction via relabeling
    relabel_configs:
      # Extract container name from metadata
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
        regex: '^/(.*)$'            # Remove leading /
        replacement: '${1}'
      
      # Extract custom labels from container
      - source_labels: ['__meta_docker_container_label_app']
        target_label: 'app'
      
      - source_labels: ['__meta_docker_container_label_logging']
        target_label: 'logging'
      
      # Set job label for all discovered containers
      - target_label: 'job'
        replacement: 'docker'
```

**Label Strategy:**
- `container`: Extracted from container name (e.g., `app-python`)
- `app`: Custom label from `docker-compose.yml` (e.g., `devops-python`)
- `job`: Fixed as `docker` for all containers
- `logging`: Filter label (only scrape containers with `logging="promtail"`)

### Docker Compose Configuration (`docker-compose.yml`)

**Resource Limits:**

| Service | CPU Limit | Memory Limit | CPU Reserve | Memory Reserve |
|---------|-----------|--------------|-------------|----------------|
| Loki | 1.0 | 1G | 0.5 | 512M |
| Promtail | 0.5 | 512M | 0.25 | 256M |
| Grafana | 1.0 | 1G | 0.5 | 512M |
| app-python | 0.5 | 512M | 0.25 | 256M |

**Health Checks:**

```yaml
# Loki health check
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s

# Grafana health check
test: ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]

# App-python health check
test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
```

**Security:**

```yaml
# Grafana environment variables
GF_AUTH_ANONYMOUS_ENABLED=false      # Require login
GF_SECURITY_ADMIN_PASSWORD=admin     # Admin credentials
GF_USERS_ALLOW_SIGN_UP=false         # No self-registration
```

---

## 4. Application Logging Implementation

### Python JSON Logging Setup

**Library:** `python-json-logger==2.0.7`

**Installation:**
```bash
pip install python-json-logger==2.0.7
```

**Implementation in `app.py`:**

```python
import json
import logging
import sys
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Add JSON formatter to handler
json_handler = logging.StreamHandler(sys.stdout)
json_formatter = jsonlogger.JsonFormatter()
json_handler.setFormatter(json_formatter)

logger.handlers.clear()
logger.addHandler(json_handler)
```

**Structured Logging Examples:**

```python
# Application startup
logger.info("Application starting", extra={
    "service": SERVICE_NAME,
    "version": SERVICE_VERSION,
    "debug": DEBUG
})

# Request logging (before_request hook)
logger.debug(
    "Request received",
    extra={
        "method": request.method,
        "path": request.path,
        "remote_addr": remote,
        "event_type": "request_received"
    }
)

# Main endpoint
logger.info(
    "Main endpoint called",
    extra={
        "event_type": "endpoint_main",
        "client_ip": client_ip,
        "status": 200
    }
)

# Error logging
logger.error(
    "Request failed",
    extra={
        "event_type": "request_error",
        "error": str(e),
        "status": 500
    }
)
```

**Log Output Example (JSON):**
```json
{"timestamp": "2026-03-11T10:15:23.456Z", "level": "INFO", "message": "Main endpoint called", "event_type": "endpoint_main", "client_ip": "172.19.0.1", "status": 200}
```

**Benefits:**
-  Structured data (easily parsed)
-  Event tracking (event_type field)
-  Context information (client_ip, status)
-  QueryableJSON parsing in LogQL (`| json`)

---

## 5. Grafana Dashboard

### Dashboard: "Devops lab7"

**4 Visualization Panels:**

#### Panel 1: Recent Logs from All Apps
- **Type:** Logs visualization
- **Query:** `{app=~"devops-.*"}`
- **Purpose:** View recent log entries with full context
- **Shows:** Timestamp, level, message, structured fields
- **Evidence Screenshot:** `graphana_raw_logs_pyapp.png`

#### Panel 2: Log Rate by App
- **Type:** Time series graph
- **Query:** `sum by(app) (rate({app=~"devops-.*"}[1m]))`
- **Purpose:** Track log volume over time
- **Y-axis:** Logs per second
- **Shows:** Traffic spikes, log volume patterns
- **Evidence Screenshot:** `rate_logs_pyapp.png`

#### Panel 3: Error Logs
- **Type:** Logs visualization
- **Query:** `{app=~"devops-.*"} | json | level="ERROR"`
- **Purpose:** Track errors from all apps
- **Shows:** Only ERROR level logs (parsed from JSON)
- **Note:** Currently empty (no errors generated in lab)
- **Evidence Screenshot:** `graphana_dashboard.png` (panel visible)

#### Panel 4: Total Log Count
- **Type:** Stat (numeric value)
- **Query:** `count_over_time({app=~"devops-.*"}[5m])`
- **Purpose:** Show total log count in current time range
- **Shows:** Single numeric value of logs over time window
- **Evidence Screenshot:** `graphana_dashboard.png` (panel visible)

**Dashboard Configuration:**
- **Name:** Devops lab7
- **Auto-refresh:** 10 seconds
- **Time range:** Last 1 hour (default)
- **Data source:** Loki
- **All panels saved** in Grafana

---

## 6. LogQL Query Language

### Query Patterns Used

#### 1. Stream Selection
```logql
{job="docker"}              # All Docker containers
{app="devops-python"}       # Only Python app
{app=~"devops-.*"}          # Regex: app starting with "devops-"
```

#### 2. Line Filtering
```logql
{app="devops-python"} |= "error"    # Contains "error"
{app="devops-python"} |= "GET"      # Contains "GET"
{app="devops-python"} != "health"   # Doesn't contain "health"
```

#### 3. JSON Parsing
```logql
{app="devops-python"} | json                    # Parse as JSON
{app="devops-python"} | json | level="ERROR"    # Filter by JSON field
{app="devops-python"} | json | status="200"     # Filter by status
```

#### 4. Metrics & Aggregation
```logql
rate({app="devops-python"}[1m])                           # Logs/sec over 1 min
sum by (app) (rate({app=~"devops-.*"}[1m]))              # Per-app rate
count_over_time({app="devops-python"}[5m])               # Total count over 5 min
sum by (level) (count_over_time({app=~".*"}[5m]))        # Count by level
```

---

## 7. Troubleshooting & Challenges

### Challenge 1: Health Check Failure (app-python unhealthy)

**Problem:**
```
app-python ... (unhealthy)
```

**Root Cause:** `curl` command not available in `python:3.13-slim` base image

**Solution:** Added to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

### Challenge 2: Loki Configuration Errors

**Problem:** Invalid config fields for Loki 3.0

**Error Examples:**
- `max_entries_limit_per_minute not found` (deprecated field)
- `shared_store not found in compactor.Config` (v3 structure change)

**Solution:** Used Loki 3.0 simplified `common:` section and updated compactor config:
```yaml
limits_config:
  retention_period: 168h  # Instead of max_entries_limit_per_minute

compactor:
  delete_request_store: filesystem  # Instead of shared_store
```


### Challenge 3: JSON Parsing in LogQL

**Problem:** Multi-line JSON logs causing parse errors

**Symptom:** Query `{app="devops-python"} | json` shows partial results

**Root Cause:** Python logger outputs both plain text AND JSON in some cases

**Solution:** 
- Used simpler queries without JSON parsing for aggregations
- For JSON extraction, used text filters first: `{app="devops-python"} |= "event_type"`
- In aggregations, avoided JSON parsing: `count_over_time({app}[5m])` instead of `count_over_time({app} | json [5m])`

---

## 8. Production Considerations

### Security Hardening

**Current (Development):**
- `auth_enabled: false` in Loki (dev only!)
- Anonymous Grafana access (was enabled during testing)

**Production Recommendations:**
```yaml
# Loki security
auth_enabled: true
authz_enabled: true

# Grafana security
GF_AUTH_ANONYMOUS_ENABLED=false
GF_SECURITY_ADMIN_PASSWORD=[strong-password]
GF_OAUTH_ENABLED=true  # Use OAuth2/SAML
```

### Data Retention

**Current:** 7 days (168 hours)
```yaml
limits_config:
  retention_period: 168h
```

**Adjustments by Use Case:**
- **Development:** 24h (1 day) - save storage
- **Staging:** 7 days (current)
- **Production:** 14-30 days (compliance requirements)

### Backup & Recovery

**Current:** No replication
```yaml
replication_factor: 1  # Single copy only
```

---


## 9. Evidence Screenshots

Located in `/labs_solution/lab7/docs/screenshots_evidence/`

| Screenshot | Purpose | Evidence For |
|------------|---------|--------------|
| `docker_ps.png` | All services healthy | Production readiness |
| `graphana_login.png` | Login page visible | Auth enabled (security) |
| `graphana_3_containers.png` | Logs from 3+ containers | Task 1 (logs flowing) |
| `graphana_raw_logs_pyapp.png` | Python app logs in Loki | Task 2 (app integration) |
| `python_json_logs.png` | JSON log structure | Task 2 (structured logs) |
| `filtered_logs_pyapp.png` | LogQL filtering works | Task 2 (query capability) |
| `rate_logs_pyapp.png` | Metrics query works | Task 3 (dashboard queries) |
| `graphana_dashboard.png` | 4-panel dashboard | Task 3 (dashboard complete) |

---
