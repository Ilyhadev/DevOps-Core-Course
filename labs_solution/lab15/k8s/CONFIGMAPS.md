# Lab 12 — ConfigMaps & Persistent Volumes

## Task 1 — Application Persistence Upgrade (2 pts) 

### Visits Counter Implementation

**Modified `app.py`:**
- Added `DATA_DIR` and `VISITS_FILE` configuration (default: `/app/data/visits`)
- `read_visits()` - reads counter from file, returns 0 if missing
- `write_visits(count)` - atomic write using temp file + rename pattern
- `/` endpoint increments counter on each access
- `/visits` endpoint returns current count
- Thread-safe with `threading.Lock()` for concurrent access

**Local Docker Testing:**

```bash
# Build and start
docker build -t devops-info-python:lab12 app_python/
docker compose up -d

# Make requests
for i in {1..5}; do curl -s http://localhost:8000/ > /dev/null; done
curl http://localhost:8000/visits
# {"visits":6}

# Check file on host
cat data/visits
# 6

# Restart container
docker compose down && sleep 2 && docker compose up -d && sleep 3

# Verify persistence
curl http://localhost:8000/visits
# {"visits":6}   ✓ PERSISTED
```

**Updated `README.md`:**
- Added `/visits` endpoint documentation
- Added visit counter persistence explanation
- Added DATA_DIR environment variable configuration

---

## Task 2 — ConfigMaps (3 pts) 

### ConfigMap Files Created

**`files/config.json`** - application configuration:
```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "kubernetes",
    "version": "1.1.0"
  },
  "features": {
    "metrics": true,
    "logging": true,
    "persistence": true
  },
  "limits": {
    "max_request_size": 1048576,
    "timeout": 30
  }
}
```

### ConfigMap Template (`templates/configmap.yaml`)

Two ConfigMaps deployed:

1. **File-based ConfigMap** - mounts `config.json`:
   - Name: `{release}-config`
   - Mounted at: `/config/config.json`

2. **Environment ConfigMap** - provides env variables:
   - Name: `{release}-env`
   - Keys: `APP_ENV`, `LOG_LEVEL`, `DATA_DIR`

### Kubernetes Verification

**ConfigMaps and PVC created:**
```
NAME                                                    DATA   AGE
configmap/devops-info-lab12-devops-info-python-config   1      62s
configmap/devops-info-lab12-devops-info-python-env      3      62s
kube-root-ca.crt                                         1      5m58s

NAME                                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/devops-info-lab12-devops-info-python-data   Bound    pvc-3ceed92a-2f1a-4488-bdaf-28aa8f658525   100Mi      RWO            standard       62s
```

**Config file inside pod:**
```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "kubernetes",
    "version": "1.1.0"
  },
  "features": {
    "metrics": true,
    "logging": true,
    "persistence": true
  },
  "limits": {
    "max_request_size": 1048576,
    "timeout": 30
  }
}
```

**Environment variables in pod:**
```
APP_ENV=kubernetes
LOG_LEVEL=INFO
DATA_DIR=/data
```

---

## Task 3 — Persistent Volumes (3 pts) 

### PVC Template (`templates/pvc.yaml`)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {release}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

**Access Mode:** `ReadWriteOnce` - single pod can mount at a time
**Storage:** 100Mi allocated, default storage class (Kind hostPath)

### Deployment Volume Mounts

**In `templates/deployment.yaml`:**
```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
  - name: data-volume
    mountPath: /data
volumes:
  - name: config-volume
    configMap:
      name: {release}-config
  - name: data-volume
    persistentVolumeClaim:
      claimName: {release}-data
```

### Persistence Test - Pod Restart

**Before pod deletion:**
```bash
$ kubectl exec -n lab12 <pod-A> -- cat /data/visits
5
```

**Pod deletion and recreation:**
```bash
$ kubectl delete pod -n lab12 devops-info-lab12-devops-info-python-5578d7f75f-kqpq2
pod "devops-info-lab12-devops-info-python-5578d7f75f-kqpq2" deleted from lab12 namespace

$ kubectl get pod -n lab12
NAME                                                    READY   STATUS    RESTARTS   AGE
devops-info-lab12-devops-info-python-5578d7f75f-lsqg9   1/1     Running   0          3m31s
devops-info-lab12-devops-info-python-5578d7f75f-n4rlt   0/1     Running   0          12s
devops-info-lab12-devops-info-python-5578d7f75f-p49mh   1/1     Running   0          3m31s
```

**Data verified on new pod (pod-B):**
```bash
$ kubectl exec -n lab12 devops-info-lab12-devops-info-python-5578d7f75f-n4rlt -- cat /data/visits
5   ✓ PERSISTED ACROSS POD RESTART
```

**PVC Status:**
```bash
$ kubectl get pvc -n lab12
NAME                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
devops-info-lab12-devops-info-python-data Bound    pvc-3ceed92a-2f1a-4488-bdaf-28aa8f658525   100Mi      RWO            standard       5m
```

---

## Task 4 — Documentation (2 pts) 

This file contains:
-  Application changes with visit counter implementation
-  Local Docker testing evidence
-  ConfigMap structure (file-based + env vars)
-  ConfigMap mounting in Deployment
-  PVC configuration & access modes
-  Volume mount setup
-  Persistence test with pod deletion evidence

---

## Summary - Checklist

| Component | Status | Evidence |
|-----------|--------|----------|
| Visits counter |  | Increments on `/` access, persists across restarts |
| `/visits` endpoint |  | Returns `{"visits": N}` |
| Docker compose volume |  | `./data:/app/data` mount verified |
| ConfigMap (file) |  | `config.json` mounted at `/config` |
| ConfigMap (env) |  | `APP_ENV`, `LOG_LEVEL`, `DATA_DIR` injected |
| PVC |  | 100Mi, ReadWriteOnce, mounted at `/data` |
| Persistence |  | Counter: 5 -> pod deleted -> new pod -> 5  |

---

## Key Files

- `app_python/app.py` - Added visits persistence
- `app_python/README.md` - Updated documentation
- `docker-compose.yml` - Volume mount for persistence
- `k8s/devops-info-python/files/config.json` - Application config
- `k8s/devops-info-python/templates/configmap.yaml` - ConfigMaps
- `k8s/devops-info-python/templates/pvc.yaml` - PersistentVolumeClaim
- `k8s/devops-info-python/templates/deployment.yaml` - Updated mounts
- `k8s/devops-info-python/values.yaml` - Persistence settings

---

## ConfigMap vs Secret

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| Use Case | Non-sensitive config | Sensitive data (passwords, API keys) |
| Encoding | Plain text | Base64 (encrypted at rest in etcd) |
| Mount Type | volumes, envFrom | volumes, envFrom |
| Size Limit | 1MB | 1MB |
| **When Used** | app settings, feature flags | credentials, tokens, certificates |


