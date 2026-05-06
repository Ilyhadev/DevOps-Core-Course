# Lab 11 - Kubernetes Secrets & HashiCorp Vault

## 1. Overview

Chart path: `labs_solution/lab11/k8s/devops-info-python` (extended from lab10)

Lab objectives:
- Kubernetes Secrets creation and consumption
- Helm-based secret management
- HashiCorp Vault integration with sidecar injection
- Resource limits configuration

Chart structure additions:
```text
devops-info-python/
├── Chart.yaml
├── values.yaml                    # UPDATED: secrets + vault config
├── templates/
│   ├── secrets.yaml               # NEW: K8s Secret template
│   ├── deployment.yaml            # UPDATED: secret refs + Vault annotations
│   ├── service.yaml
│   ├── _helpers.tpl
│   └── NOTES.txt
└── ...
```

---

## 2. Task 1: Kubernetes Secrets Fundamentals

### Requirements
- Create secret named `app-credentials` with `username` and `password` keys
- View secret in YAML and decode base64 values
- Understand encryption vs encoding

### Key Concepts

**Base64 Encoding vs Encryption:**
- Base64 is **encoding** (easily reversible)
- Kubernetes Secrets are NOT encrypted at rest by default
- etcd encryption must be explicitly enabled for production

**Security Model:**
Kubernetes Secrets are stored in etcd as base64-encoded strings. Anyone with API access can decode them.

---

## 3. Task 2: Helm-Managed Secrets

### Requirements
- Create `templates/secrets.yaml`
- Define secrets in `values.yaml`
- Inject secrets as environment variables
- Configure resource limits

### Configuration Files

**values.yaml - Secrets Section:**
```yaml
secrets:
  enabled: true
  username: "admin"
  password: "changeme123"
  databaseUrl: "postgresql://localhost:5432/app"
  apiKey: "api-key-placeholder"

resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "250m"
    memory: "256Mi"
```

**templates/secrets.yaml:**
```yaml
{{- if .Values.secrets.enabled }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-python.fullname" . }}-app-credentials
  labels:
    {{- include "devops-info-python.labels" . | nindent 4 }}
  namespace: {{ .Release.Namespace }}
type: Opaque
stringData:
  username: {{ .Values.secrets.username | quote }}
  password: {{ .Values.secrets.password | quote }}
  database-url: {{ .Values.secrets.databaseUrl | quote }}
  api-key: {{ .Values.secrets.apiKey | quote }}
{{- end }}
```

**templates/deployment.yaml - Secret Injection:**

Added to the `env` section:
```yaml
{{- if .Values.secrets.enabled }}
- name: APP_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-python.fullname" . }}-app-credentials
      key: username
- name: APP_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-python.fullname" . }}-app-credentials
      key: password
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-python.fullname" . }}-app-credentials
      key: database-url
- name: API_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-python.fullname" . }}-app-credentials
      key: api-key
{{- end }}
```

**Resource Limits Explanation:**

| Parameter | Purpose | Value |
|-----------|---------|-------|
| Requests (CPU) | Guaranteed CPU for scheduling | 100m |
| Requests (Memory) | Guaranteed memory for scheduling | 128Mi |
| Limits (CPU) | Maximum CPU the pod can use | 250m |
| Limits (Memory) | Maximum memory before termination | 256Mi |

---

## 4. Task 3: HashiCorp Vault Integration

### Requirements
- Install Vault via Helm with agent injector
- Enable KV v2 secrets engine
- Configure Kubernetes authentication
- Create policy and role
- Enable agent sidecar injection

### Configuration

**values.yaml - Vault Section:**
```yaml
vault:
  enabled: true
  role: "devops-info-python"
  secretPath: "secret/data/myapp/config"
```

**templates/deployment.yaml - Vault Annotations:**

Added to pod metadata:
```yaml
{{- if .Values.vault.enabled }}
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
  vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
  vault.hashicorp.com/agent-inject-template-config: |
    {{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}
    export VAULT_USERNAME="{{ .Data.data.username }}"
    export VAULT_PASSWORD="{{ .Data.data.password }}"
    export VAULT_DB_URL="{{ .Data.data.db_url }}"
    export VAULT_API_KEY="{{ .Data.data.api_key }}"
    {{- end }}`}}
{{- end }}
```

**Sidecar Injection Pattern:**

The Vault Agent Injector webhook intercepts pod creation and:
1. Injects init container for authentication
2. Injects sidecar for secret retrieval
3. Mounts secrets at `/vault/secrets/`

---

## 5. Security Analysis

### Kubernetes Secrets vs Vault

| Aspect | K8s Secrets | Vault |
|--------|------------|-------|
| Encryption at Rest | Optional | Built-in |
| Secret Rotation | Manual | Automatic |
| Audit Logging | Limited | Comprehensive |
| Access Control | RBAC (namespace) | Fine-grained policies |
| Use Case | Dev/Test | Production |

### Production Recommendations

**Use Kubernetes Secrets when:**
- Development/testing environment
- Infrastructure has etcd encryption enabled
- Non-sensitive configuration

**Use HashiCorp Vault when:**
- Production with compliance requirements
- Need automatic secret rotation
- Multi-environment management
- Advanced audit tracking required

---

## 6. Evidence & Verification

### Task 1 - Kubernetes Secrets Creation

Command to create secret:
```bash
kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=secretPass123 --dry-run=client -o yaml
```

**Output:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-credentials
type: Opaque
data:
  password: c2VjcmV0UGFzczEyMw==
  username: YWRtaW4=
```

Command to decode base64:
```bash
echo "c2VjcmV0UGFzczEyMw==" | base64 -d
echo "YWRtaW4=" | base64 -d
```

**Output:** 
```
secretPass123
admin
```

**Finding:** Base64 is easily reversible - Secrets are NOT encrypted by default!

### Task 2 - Helm Chart Validation

Lint command:
```bash
helm lint ./devops-info-python
```

**Output:**
```
==> Linting ./devops-info-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Verify secret in K8s namespace:
```bash
kubectl get secret -n lab11 devops-info-python-app-credentials
```

**Output:**
```
NAME                                 TYPE     DATA   AGE
devops-info-python-app-credentials   Opaque   4      5m28s
```

Check K8s Secret environment variables in pod:
```bash
POD=$(kubectl get pods -n lab11 -l app.kubernetes.io/name=devops-info-python -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n lab11 $POD -- env | grep -E "APP_|DATABASE_|API_"
```

**Output:**
```
API_KEY=api-key-placeholder
APP_USERNAME=admin
APP_PASSWORD=changeme123
DATABASE_URL=postgresql://localhost:5432/app
```

Verify resource limits applied:
```bash
POD=$(kubectl get pods -n lab11 -l app.kubernetes.io/name=devops-info-python -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod -n lab11 $POD | grep -A 5 "devops-info-python:" | grep -A 5 "Limits"
```

**Output (Application Container):**
```
    Limits:
      cpu:     250m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
```

Resource limits properly configured in pod!

### Task 3 - Vault Installation & Configuration

Installation commands:
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault --set "server.dev.enabled=true" --set "injector.enabled=true"
kubectl get pods -l app.kubernetes.io/name=vault
```

**Output:**
```
"hashicorp" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorp" chart repository
Update Complete. ⎈Happy Helming!⎈
NAME: vault
LAST DEPLOYED: Wed Apr  8 11:51:05 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1

NAME      READY   STATUS    RESTARTS   AGE
vault-0   1/1     Running   0          2m
vault-agent-injector-xxxxx-xxxxx   1/1     Running   0          2m
```

Vault configuration (enable KV secrets and create secret):
```bash
kubectl exec -it vault-0 -- sh -c 'vault secrets enable -path=secret kv-v2'
kubectl exec -it vault-0 -- sh -c 'vault kv put secret/myapp/config username=admin password=vaultSecret123 db_url=postgresql://vault-db:5432/myapp api_key=vault-api-key-xyz789'
kubectl exec -it vault-0 -- sh -c 'vault auth enable kubernetes'
```

**Output:**
```
Success! Enabled the kv-v2 secrets engine at: secret/

======= Secret Path =======
secret/data/myapp/config

===== Data =====
Key         Value
---         -----
api_key     vault-api-key-xyz789
db_url      postgresql://vault-db:5432/myapp
password    vaultSecret123
username    admin

Success! Enabled kubernetes auth method at: kubernetes/
```

Configure Kubernetes auth, create policy and role:
```bash
kubectl exec -it vault-0 -- sh -c 'vault write auth/kubernetes/config kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT" kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token'

kubectl exec -it vault-0 -- sh -c 'vault policy write devops-info-python - << EOF
path "secret/data/myapp/config" {
  capabilities = ["read", "list"]
}
path "secret/metadata/myapp/config" {
  capabilities = ["read", "list"]
}
EOF'

kubectl exec -it vault-0 -- sh -c 'vault write auth/kubernetes/role/devops-info-python bound_service_account_names=default bound_service_account_namespaces=default,lab11 policies=devops-info-python ttl=24h'
```

**Output:**
```
Success! Data written to: auth/kubernetes/config
Success! Uploaded policy: devops-info-python
Success! Data written to: auth/kubernetes/role/devops-info-python
```

Deploy application with Vault annotations:
```bash
kubectl create namespace lab11
helm install devops-info-python /path/to/devops-info-python -n lab11 --set service.nodePort=30082
```

**Output:**
```
namespace/lab11 created
NAME: devops-info-python
LAST DEPLOYED: Wed Apr  8 11:54:52 2026
NAMESPACE: lab11
STATUS: deployed
REVISION: 1
```

Verify Vault Agent sidecar injection:
```bash
kubectl get pods -n lab11 -o wide
```

**Output:**
```
NAME                                  READY   STATUS    RESTARTS   AGE   IP            NODE
devops-info-python-8486df5655-b5wwg   2/2     Running   0          48s   10.244.0.27   devops-lab9-control-plane
devops-info-python-8486df5655-s6thd   2/2     Running   0          48s   10.244.0.26   devops-lab9-control-plane
devops-info-python-8486df5655-wnbgd   2/2     Running   0          48s   10.244.0.28   devops-lab9-control-plane
```

2/2 containers = app + Vault Agent sidecar!

Verify Vault-injected secrets file:
```bash
POD=$(kubectl get pods -n lab11 -l app.kubernetes.io/name=devops-info-python -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n lab11 $POD -- cat /vault/secrets/config
```

**Output:**
```
export VAULT_USERNAME="admin"
export VAULT_PASSWORD="vaultSecret123"
export VAULT_DB_URL="postgresql://vault-db:5432/myapp"
export VAULT_API_KEY="vault-api-key-xyz789"
```

Vault secrets successfully injected at `/vault/secrets/config`!
