# Lab 13 - GitOps with ArgoCD

## 1. Overview

This lab implements GitOps principles using ArgoCD, a declarative continuous delivery tool for Kubernetes. The deployment manifests are defined in Git, and ArgoCD ensures the cluster state matches the desired state in the repository.

### Architecture
```
Git Repository (Source of Truth)
    ↓
    ├── Helm Chart (k8s/devops-info-python/)
    ├── Application Manifests (k8s/argocd/)
    ├── Environment Configs (values-dev.yaml, values-prod.yaml)
    │
ArgoCD Server (In Cluster)
    ├── Polls Git every 3 minutes
    ├── Renders Helm templates
    ├── Detects configuration drift
    ├── Auto-syncs or waits for manual approval
    │
Kubernetes Cluster
    ├── Dev Namespace (auto-sync enabled)
    ├── Prod Namespace (manual sync)
    └── Default Namespace
```

---

## 2. ArgoCD Setup & Installation

### 2.1 Installation Steps

**1. Add Helm Repository:**
```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

**2. Create Namespace:**
```bash
kubectl create namespace argocd
```

**3. Install ArgoCD via Helm:**
```bash
helm install argocd argo/argo-cd \
  --namespace argocd \
  --set configs.params."server\.insecure"=true
```

**4. Wait for All Components Ready:**
```bash
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=120s

kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-repo-server \
  -n argocd --timeout=120s

kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=argocd-application-controller \
  -n argocd --timeout=120s
```

**5. Verify Installation:**
```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
```

**Expected Output:**
```
NAME                                    READY   STATUS    RESTARTS   AGE
argocd-application-controller-0         1/1     Running   0          2m
argocd-applicationset-controller-0      1/1     Running   0          2m
argocd-dex-server-7f8d4bc6-5kq7b        1/1     Running   0          2m
argocd-notifications-controller-0       1/1     Running   0          2m
argocd-redis-0                          1/1     Running   0          2m
argocd-repo-server-64f8479775-5kq7b     1/1     Running   0          2m
argocd-server-d97947bf9-5kq7b           1/1     Running   0          2m
```

### 2.2 UI Access

**1. Port Forward to ArgoCD Server:**
```bash
# Run in a separate terminal
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**2. Retrieve Initial Admin Password:**
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

**3. Access UI:**
- Open browser: `https://localhost:8080`
- Username: `admin`
- Password: (from previous command)
- Accept self-signed certificate warning

### 2.3 CLI Setup

**1. Install ArgoCD CLI:**
```bash
# macOS
brew install argocd

# Linux - Download latest release
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
rm argocd-linux-amd64
```

**2. Login via CLI:**
```bash
argocd login localhost:8080 --insecure
# Username: admin
# Password: (from kubectl secret above)
```

**3. Verify CLI Connection:**
```bash
argocd version
argocd server info
```

---

## 3. Application Configuration

### 3.1 Application Manifest Structure

**File:** `k8s/argocd/application.yaml`

Key components:
- **metadata.name:** Unique identifier for the application in ArgoCD
- **metadata.namespace:** Must be `argocd` (ArgoCD namespace)
- **spec.project:** Default or custom ArgoCD project
- **spec.source.repoURL:** Git repository URL
- **spec.source.targetRevision:** Branch or tag (e.g., `lab13`)
- **spec.source.path:** Path to Helm chart in repository
- **spec.source.helm.valueFiles:** Values files to use (order matters)
- **spec.destination.server:** Kubernetes API server
- **spec.destination.namespace:** Target namespace for deployment
- **spec.syncPolicy:** Sync behavior and options

### 3.2 Helm Integration

ArgoCD renders Helm templates using specified values files:

```yaml
source:
  helm:
    valueFiles:
      - values.yaml              # Base configuration
      - values-dev.yaml          # Dev overrides (if applicable)
```

Values are merged in order: base → environment-specific.

### 3.3 Values Files

**values.yaml (Default):**
- 3 replicas
- NodePort service
- Standard resource requests/limits

**values-dev.yaml (Development):**
- 1 replica (minimal resource usage)
- NodePort service
- Reduced CPU/memory requirements

**values-prod.yaml (Production):**
- 5 replicas (high availability)
- LoadBalancer service (external access)
- Increased resource requirements

---

## 4. Multi-Environment Deployment

### 4.1 Environment Setup

**1. Create Namespaces:**
```bash
kubectl create namespace dev
kubectl create namespace prod
```

**2. Verify Namespaces:**
```bash
kubectl get namespaces
```

### 4.2 Application Manifests

#### Dev Environment (Auto-Sync)
**File:** `k8s/argocd/application-dev.yaml`

```yaml
spec:
  syncPolicy:
    automated:
      prune: true      # Delete resources removed from Git
      selfHeal: true   # Revert manual cluster changes
```

**Benefits:**
- Immediate synchronization with Git changes
- Self-healing prevents configuration drift
- Ideal for non-critical environments

#### Prod Environment (Manual Sync)
**File:** `k8s/argocd/application-prod.yaml`

```yaml
spec:
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
  # No automated policy = manual sync required
```

**Benefits:**
- Change review before deployment
- Controlled release timing
- Compliance and audit trail
- Rollback planning

### 4.3 Deployment Steps

**1. Create Applications:**
```bash
kubectl apply -f k8s/argocd/application-dev.yaml
kubectl apply -f k8s/argocd/application-prod.yaml
```

**2. Verify in ArgoCD UI:**
- Applications should appear in UI
- Check sync status for each

**3. Perform Initial Sync:**
```bash
# Dev (may auto-sync)
argocd app sync python-app-dev

# Prod (manual)
argocd app sync python-app-prod
```

**4. Monitor Deployment:**
```bash
argocd app get python-app-dev
argocd app get python-app-prod

# Watch resources
kubectl get pods -n dev -w
kubectl get pods -n prod -w
```

### 4.4 Configuration Differences

| Aspect | Dev | Prod |
|--------|-----|------|
| **Replicas** | 1 | 5 |
| **Service Type** | NodePort | LoadBalancer |
| **CPU Request** | 50m | 200m |
| **Memory Request** | 64Mi | 256Mi |
| **CPU Limit** | 100m | 500m |
| **Memory Limit** | 128Mi | 512Mi |
| **Sync Policy** | Automated | Manual |
| **Self-Heal** | Enabled | N/A |

---

## 5. Self-Healing & Sync Policies

### 5.1 Self-Healing Test

**Objective:** Verify ArgoCD automatically reverts manual cluster changes

**Test 1: Manual Replica Scale**

1. Scale deployment manually:
```bash
kubectl scale deployment python-app-dev -n dev --replicas=5
kubectl get pods -n dev
```

Expected: 5 pods running

2. Observe ArgoCD detecting drift:
```bash
argocd app get python-app-dev
```

Expected output shows: `OutOfSync` status

3. Watch self-healing revert:
```bash
kubectl get pods -n dev -w
```

Expected: Within ~3 minutes, pods revert to 1 replica

4. Verify sync restored:
```bash
argocd app get python-app-dev
```

Expected: `Synced` status

**Test 2: Pod Deletion**

1. Delete a pod:
```bash
kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-python
```

2. Observe recreation:
```bash
kubectl get pods -n dev -w
```

Expected: Pod is immediately recreated by ReplicaSet

**Note:** This is Kubernetes behavior (ReplicaSet controller), not ArgoCD self-healing.

**Test 3: Configuration Drift**

1. Manually add label to deployment:
```bash
kubectl patch deployment python-app-dev -n dev \
  -p '{"spec":{"template":{"metadata":{"labels":{"manual":"test"}}}}}'
```

2. View diff in ArgoCD:
```bash
argocd app diff python-app-dev
```

Expected: Diff shows the added label

3. Self-heal reverts:
```bash
# After ~3 minutes, check status
argocd app get python-app-dev
```

Expected: Label removed, `Synced` status

### 5.2 Sync Behavior Explanation

**Kubernetes Self-Healing (ReplicaSet/Deployment):**
- Maintains desired pod count
- Automatic and continuous
- Replaces failed/deleted pods
- Example: Pod crashes → new pod created

**ArgoCD Self-Healing:**
- Ensures cluster matches Git state
- Runs every sync interval (~3 minutes)
- Reverts manual resource edits
- Removes resources not in Git

**Sync Triggers:**
- **Automated:** Every 3 minutes (default) or via webhook
- **Manual:** `argocd app sync` or UI button
- **Webhook:** Git commit push triggers immediate sync

**Sync States:**
- **Synced:** Cluster matches Git
- **OutOfSync:** Git has changes not applied
- **Unknown:** Unable to determine state
- **Progressing:** Sync in progress
- **Healthy:** Application running correctly
- **Degraded:** Application not healthy

### 5.3 Manual vs Automated Sync

**Automated Sync (Dev):**
- Enabled via `syncPolicy.automated`
- `prune: true` - deletes removed resources
- `selfHeal: true` - reverts manual changes
- Suitable for non-prod environments

**Manual Sync (Prod):**
- No automated sync policy
- Requires explicit trigger
- Change review before sync
- Better for compliance/audit

---

## 6. GitOps Workflow Example

### 6.1 Making a Change

**Step 1: Update Chart in Git**
```bash
# Edit values-prod.yaml
# Change: replicaCount: 5 → 6
git add k8s/devops-info-python/values-prod.yaml
git commit -m "Increase prod replicas to 6"
git push origin lab13
```

**Step 2: ArgoCD Detects Change**
```bash
# ArgoCD polls Git every 3 minutes
# Or trigger immediate sync:
argocd app refresh python-app-prod

# Wait a moment for repo-server to fetch
sleep 5

# Check status
argocd app get python-app-prod
```

Expected: `OutOfSync` status

**Step 3: Manual Approval (Prod)**
```bash
# Review changes
argocd app diff python-app-prod

# Approve and sync
argocd app sync python-app-prod
```

**Step 4: Verify Deployment**
```bash
# Watch new pods appear
kubectl get pods -n prod -w

# Confirm final state
kubectl get deployment -n prod
argocd app get python-app-prod
```

Expected: 6 replicas running, `Synced` status

### 6.2 Automatic Sync (Dev)

Same process, but sync happens automatically:
- No manual sync required
- Immediate after change pushed
- Suitable for dev/test environments

---

## 7. Advanced Features

### 7.1 ApplicationSet (Bonus)

**File:** `k8s/argocd/applicationset.yaml`

ApplicationSet generates multiple applications from a template:

```yaml
generators:
  - list:
      elements:
        - env: dev
          namespace: dev
          valuesFile: values-dev.yaml
          autoSync: "true"
        - env: prod
          namespace: prod
          valuesFile: values-prod.yaml
          autoSync: "false"
```

**Benefits:**
- Single template for multiple environments
- Reduces manifest duplication
- Easier maintenance and updates
- Supports multi-cluster deployments

**Deploy ApplicationSet:**
```bash
kubectl apply -f k8s/argocd/applicationset.yaml

# Verify generated applications
argocd app list | grep python-app
kubectl get applications -n argocd
```

Expected: Two applications automatically created from template

### 7.2 Sync Waves (Optional)

For dependent resources, use sync waves:
```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"  # Deploy first
```

Lower values deploy first.

### 7.3 Notifications (Optional)

Configure alerts for sync events:
- Slack
- Email
- Webhooks
- Various integrations

---

## 8. Troubleshooting

### Issue: Application stuck in "Progressing" state
```bash
# Check pod status
kubectl get pods -n argocd

# Check repo-server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server -f

# Manually refresh
argocd app refresh python-app-dev
```

### Issue: "Unknown" sync status
```bash
# Verify Git repository is accessible
argocd repo list

# Check if chart path exists in repo
git ls-remote <repo-url> | head

# Check Helm chart validity
helm lint k8s/devops-info-python/
```

### Issue: Self-heal not working
```bash
# Verify auto-sync enabled
argocd app get <app-name> | grep -A5 syncPolicy

# Check ArgoCD controller logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller -f
```

---

## 9. Key Concepts Summary

### GitOps Principles
1. **Declarative:** Define desired state in Git
2. **Versioned & Immutable:** Git history tracks all changes
3. **Pulled Automatically:** ArgoCD pulls from Git (vs push)
4. **Continuously Reconciled:** Cluster constantly syncs with Git

### ArgoCD Components
- **API Server:** REST API and Web UI
- **Repo Server:** Fetches Git repos and renders manifests
- **Application Controller:** Monitors apps and syncs state
- **Redis:** Caching and state management

### Sync Policies
- **Manual:** Requires explicit approval
- **Automated:** Automatic with optional prune/selfHeal
- **Hybrid:** Different policies per environment

---

## 10. References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Application CRD](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)
- [Sync Policies](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)
- [ApplicationSet](https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/)
- [GitOps Principles](https://opengitops.dev/)

---

## Checklist

### Installation & Access
- [x] ArgoCD installed via Helm
- [x] All pods running in argocd namespace
- [x] UI accessible via port-forward (https://localhost:8080)
- [x] Admin password retrieved and changed
- [x] CLI installed and logged in

### Application Deployment
- [x] `k8s/argocd/` directory created
- [x] Application manifests created (application.yaml, application-dev.yaml, application-prod.yaml)
- [x] Applications visible in ArgoCD UI
- [x] Initial sync completed
- [x] App accessible and working
- [x] GitOps workflow tested

### Multi-Environment
- [x] Dev and prod namespaces created
- [x] Dev application with auto-sync and self-heal
- [x] Prod application with manual sync
- [x] Different resource configurations per environment
- [x] Both apps deployed and verified

### Self-Healing & Documentation
- [x] Manual scale test performed
- [x] Self-healing observed and documented
- [x] Pod deletion test performed
- [x] Configuration drift test done
- [x] Behavior differences documented

### Bonus
- [x] ApplicationSet manifest created
- [x] Multiple apps generated from template
- [x] Generator configuration documented
- [x] Benefits explained

---

**Last Updated:** Lab 13 - GitOps with ArgoCD
**Version:** 1.0
