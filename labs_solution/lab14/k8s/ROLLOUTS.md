# Lab 14 — Progressive Delivery with Argo Rollouts
---

## Argo Rollouts Setup

### Install controller (and verify CRDs)

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl wait --for=condition=available --timeout=180s deployment/argo-rollouts -n argo-rollouts
```

Verified:
- `customresourcedefinitions ... rollouts.argoproj.io` created
- `deployment/argo-rollouts` became `available`

### Install `kubectl argo rollouts` plugin

Because `/usr/local/bin` was not writable in this environment, the plugin was installed to user-local bin:

```bash
mkdir -p "$HOME/.local/bin"
install -m 0755 kubectl-argo-rollouts-linux-amd64 "$HOME/.local/bin/kubectl-argo-rollouts"
export PATH="$HOME/.local/bin:$PATH"

kubectl argo rollouts version
```

### Install dashboard

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl wait --for=condition=available --timeout=180s deployment/argo-rollouts-dashboard -n argo-rollouts
```

---

## Task 2 — Canary Deployment (promotion + abort)

### Canary strategy configuration (what to look for)

In `k8s/devops-info-python/templates/rollout.yaml`:
- `kind: Rollout`
- `spec.strategy.canary.steps` uses:
  - `setWeight: 20` then `pause: {}`
  - `setWeight: 40` then `pause: { duration: 30s }`
  - `setWeight: 60` then `pause: { duration: 30s }`
  - `setWeight: 80` then `pause: { duration: 30s }`
  - `setWeight: 100`

### Deploy the initial canary (stable baseline)

```bash
helm upgrade --install devops-info-python ./k8s/devops-info-python --namespace default
kubectl argo rollouts get rollout devops-info-python --watch=false
```

### Trigger a new canary revision

```bash
helm upgrade devops-info-python ./k8s/devops-info-python \
  --namespace default \
  --set-string image.tag=lab14-v2
```

Then corrected the image/environment and continued the canary with:

```bash
helm upgrade devops-info-python ./k8s/devops-info-python \
  --namespace default \
  --set-string image.tag=latest \
  --set-json 'env=[{"name":"PORT","value":"8080"},{"name":"DEBUG","value":"true"}]'
```

Rollout became **paused** at the manual step:
- `Message: CanaryPauseStep`

### **Promotion + abort demonstration**

Promotion:

```bash
kubectl argo rollouts promote devops-info-python
kubectl argo rollouts get rollout devops-info-python --watch=false
```

Abort:

```bash
kubectl argo rollouts abort devops-info-python
kubectl argo rollouts get rollout devops-info-python --watch=false
```

**Screenshot**
- **Task 2 / Promotion+Abort**: terminal output shows both:
  - `rollout 'devops-info-python' promoted` (paused canary step)
  - `rollout 'devops-info-python' aborted` + `Status: ✖ Degraded` with `RolloutAborted`

See folder `screenshots/` to check evidence.
### Why `Degraded` + `RolloutAborted` is expected

When i run `kubectl argo rollouts abort` during an in-progress canary:
- Argo Rollouts stops the current update (the canary revision that was being rolled out).
- It reverts traffic/state to the stable revision as part of the abort recovery.

During this reconciliation window Argo reports the rollout as **degraded** and includes the message **`RolloutAborted`** because the update process was explicitly terminated and the controller is transitioning back to the stable state.

---

## Task 3 — Blue-Green Deployment (promotion + instant rollback)

### Configure blue-green strategy

Blue-green config is provided by:
- `k8s/devops-info-python/values-bluegreen.yaml`

It sets:
- `rollout.strategy: blueGreen`
- `rollout.blueGreen.autoPromotionEnabled: false` (manual promotion)

### Deploy the “blue” (active) version

```bash
helm upgrade devops-info-python ./k8s/devops-info-python \
  --namespace default \
  -f ./k8s/devops-info-python/values-bluegreen.yaml \
  --set-string image.tag=latest \
  --set-json 'env=[{"name":"PORT","value":"8080"},{"name":"DEBUG","value":"false"}]'
```

Verify:
```bash
kubectl argo rollouts get rollout devops-info-python --watch=false
```

### Trigger the “green” (preview) version

```bash
helm upgrade devops-info-python ./k8s/devops-info-python \
  --namespace default \
  -f ./k8s/devops-info-python/values-bluegreen.yaml \
  --set-string image.tag=latest \
  --set-json 'env=[{"name":"PORT","value":"8080"},{"name":"DEBUG","value":"true"}]'
```

The rollout should pause with a message like:
- `Message: BlueGreenPause`

### **Promotion process**

Promote green to active:

```bash
kubectl argo rollouts promote devops-info-python
kubectl argo rollouts get rollout devops-info-python --watch=false
```

**Screenshots**
- **Task 3 / Promotion process**: terminal output showing:
  - `rollout 'devops-info-python' promoted`
  - `Status: ✔ Healthy`
  - `Strategy: BlueGreen`

See folder `screenshots/` to check evidence.
### Instant rollback verification

After green was promoted to active, rollback was performed using `undo` and then promotion to finalize the manual cutover:

```bash
kubectl argo rollouts undo devops-info-python
kubectl argo rollouts get rollout devops-info-python --watch=false

# finalize the cutover (manual promotion because autoPromotionEnabled=false)
kubectl argo rollouts promote devops-info-python
kubectl argo rollouts get rollout devops-info-python --watch=false
```

The expected outcome is that the rollout returns to the previous stable version with an (all-at-once) traffic switch characteristic of blue-green.

---

## CLI Commands Reference

Useful commands used in this lab:

```bash
# Watch rollout progress
kubectl argo rollouts get rollout devops-info-python -w

# One-shot status
kubectl argo rollouts get rollout devops-info-python --watch=false

# Manual canary step promotion
kubectl argo rollouts promote devops-info-python

# Abort in-progress update
kubectl argo rollouts abort devops-info-python

# Blue-green rollback
kubectl argo rollouts undo devops-info-python
```

---

## Strategy Comparison

- **Canary**
  - Gradual traffic shifting (percentage-based).
  - Better when you want early exposure to a small subset of users and step-by-step control.
  - Failures can limit blast radius.

- **Blue-Green**
  - Instant all-or-nothing switch to the new version.
  - Better when you need fast cutover and easy rollback using two fixed environments (active vs preview).
  - Requires extra resources during overlap.

