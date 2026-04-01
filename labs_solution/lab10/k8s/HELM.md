# Lab 10 - Helm Package Manager

## 1. Chart Overview

Chart path:
- `labs_solution/lab10/k8s/devops-info-python`

Helm concepts summary:
- `Chart`: a versioned package of Kubernetes templates and default values.
- `Release`: a deployed instance of a chart in a cluster namespace.
- `Repository`: a remote index/storage for published charts.
- `Values`: configuration inputs merged from `values.yaml`, extra `-f` files, and `--set`.

Helm architecture summary:
- Helm CLI renders chart templates locally using values.
- Rendered manifests are sent to Kubernetes API server.
- Release state/history is stored in-cluster and managed with `install/upgrade/rollback/uninstall`.

Chart structure:

```text
devops-info-python/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── hooks/
    │   ├── pre-install-job.yaml
    │   └── post-install-job.yaml
    └── NOTES.txt
```

Key template files and purpose:
- `templates/deployment.yaml`: deployment converted from Lab 9 manifest and templated.
- `templates/service.yaml`: service type/ports templated (NodePort and LoadBalancer use cases).
- `templates/_helpers.tpl`: naming and labels helper templates.
- `templates/hooks/pre-install-job.yaml`: pre-install validation job hook.
- `templates/hooks/post-install-job.yaml`: post-install smoke-check job hook.

## 2. Configuration Guide

Important values:
- `replicaCount`
- `image.repository`, `image.tag`, `image.pullPolicy`
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`
- `resources.requests`, `resources.limits`
- `livenessProbe`, `readinessProbe`
- `hooks.*`

Documentation of differences (dev vs prod):

| Parameter | Dev (`values-dev.yaml`) | Prod (`values-prod.yaml`) | Why |
|---|---|---|---|
| `replicaCount` | `1` | `5` | Dev is lightweight, prod is highly available |
| `service.type` | `NodePort` | `LoadBalancer` | Local access in dev, external-ready in prod |
| `service.nodePort` | `30081` | `null` | Fixed dev port, omitted for LB |
| `resources.requests.cpu` | `50m` | `200m` | Lower dev baseline |
| `resources.requests.memory` | `64Mi` | `256Mi` | Lower dev baseline |
| `resources.limits.cpu` | `100m` | `500m` | Higher prod limits |
| `resources.limits.memory` | `128Mi` | `512Mi` | Higher prod limits |
| `livenessProbe.initialDelaySeconds` | `5` | `30` | Faster dev iteration vs prod warmup |
| `readinessProbe.initialDelaySeconds` | `3` | `10` | Faster dev readiness vs safer prod warmup |

Command:

```bash
helm get values lab10-app
```

Output:

```text
USER-SUPPLIED VALUES:
image:
  tag: lab9
livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 5
readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 3
replicaCount: 5
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  nodePort: null
  port: 80
  targetPort: 8080
  type: LoadBalancer
```

## 3. Hook Implementation

Implemented hooks:
- Pre-install hook with weight `-5` and deletion policy `before-hook-creation,hook-succeeded`.
- Post-install hook with weight `5` and deletion policy `before-hook-creation,hook-succeeded`.

Dry-run hook verification command:

```bash
helm install --dry-run=client --debug lab10-dev-check labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-dev.yaml
```

Output (key lines):

```text
7:STATUS: pending-install
109:    "helm.sh/hook": post-install
110:    "helm.sh/hook-weight": "5"
111:    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
145:    "helm.sh/hook": pre-install
146:    "helm.sh/hook-weight": "-5"
147:    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

On-cluster hook execution/deletion verification commands:

```bash
kubectl get jobs -l app.kubernetes.io/instance=lab10-app
kubectl get job lab10-app-devops-info-python-pre-install
kubectl get job lab10-app-devops-info-python-post-install
kubectl describe job lab10-app-devops-info-python-pre-install
kubectl describe job lab10-app-devops-info-python-post-install
kubectl get events --sort-by=.metadata.creationTimestamp | tail -n 40
```

Output:

```text
No resources found in default namespace.

Error from server (NotFound): jobs.batch "lab10-app-devops-info-python-pre-install" not found
Error from server (NotFound): jobs.batch "lab10-app-devops-info-python-post-install" not found
Error from server (NotFound): jobs.batch "lab10-app-devops-info-python-pre-install" not found
Error from server (NotFound): jobs.batch "lab10-app-devops-info-python-post-install" not found

... Normal    Completed    job/lab10-app-devops-info-python-pre-install   Job completed
... Normal    Completed    job/lab10-app-devops-info-python-post-install  Job completed
```

## 4. Installation Evidence

### Helm Fundamentals

Commands:

```bash
helm version
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo update
helm search repo prometheus-community/prometheus
helm show chart prometheus-community/prometheus
```

Output:

```text
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}

"prometheus-community" already exists with the same configuration, skipping

Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈

NAME                                               CHART VERSION APP VERSION DESCRIPTION
prometheus-community/prometheus                    28.14.1       v3.10.0    Prometheus is a monitoring system and time series database.
...

apiVersion: v2
name: prometheus
type: application
version: 28.14.1
appVersion: v3.10.0
```

### Dev Install Evidence

Commands:

```bash
helm uninstall lab10-app || true
helm install lab10-app labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-dev.yaml --wait --wait-for-jobs --timeout 180s
helm list
kubectl get all -l app.kubernetes.io/instance=lab10-app -o wide
```

Output:

```text
release "lab10-app" uninstalled

NAME: lab10-app
LAST DEPLOYED: Wed Apr  1 10:31:59 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete

NAME      NAMESPACE REVISION UPDATED                                 STATUS   CHART                    APP VERSION
lab10-app default   1        2026-04-01 10:31:59.942315275 +0300 MSK deployed devops-info-python-0.1.0 lab9

NAME                                                READY   STATUS    RESTARTS      AGE   IP            NODE
pod/lab10-app-devops-info-python-7976578f79-wwdws   1/1     Running   2 (43s ago)   2m    10.244.0.23   devops-lab9-control-plane

NAME                                   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab10-app-devops-info-python   NodePort   10.96.192.136   <none>        80:30081/TCP   2m

NAME                                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-app-devops-info-python   1/1     1            1           2m
```

### Prod Upgrade Evidence

Commands:

```bash
helm upgrade lab10-app labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-prod.yaml --wait --timeout 240s
kubectl get deploy,svc -l app.kubernetes.io/instance=lab10-app -o wide
```

Output:

```text
Release "lab10-app" has been upgraded. Happy Helming!
NAME: lab10-app
LAST DEPLOYED: Wed Apr  1 10:34:07 2026
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete

NAME                                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-app-devops-info-python   5/5     5            5           3m5s

NAME                                   TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab10-app-devops-info-python   LoadBalancer   10.96.192.136   <pending>     80:30081/TCP   3m5s
```

## 5. Operations

Installation operation command and output:

```bash
helm install lab10-app labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-dev.yaml --wait --wait-for-jobs --timeout 180s
```

```text
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

Upgrade operation command and output:

```bash
helm upgrade lab10-app labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-prod.yaml --wait --timeout 240s
```

```text
Release "lab10-app" has been upgraded. Happy Helming!
REVISION: 2
DESCRIPTION: Upgrade complete
```

Rollback operation command and output:

```bash
helm rollback lab10-app 1
kubectl get deploy,svc -l app.kubernetes.io/instance=lab10-app -o wide
helm rollback lab10-app 2
kubectl get deploy,svc -l app.kubernetes.io/instance=lab10-app -o wide
```

```text
Rollback was a success! Happy Helming!

(deployment after rollback to 1)
deployment.apps/lab10-app-devops-info-python   1/1     1            1           6m4s   devops-info-python   devops-info-python:lab9   app.kubernetes.io/instance=lab10-app,app.kubernetes.io/name=devops-info-python
service/lab10-app-devops-info-python           NodePort 10.96.192.136 <none> 80:30081/TCP 6m4s app.kubernetes.io/instance=lab10-app,app.kubernetes.io/name=devops-info-python

Rollback was a success! Happy Helming!

(deployment after rollback to 2)
deployment.apps/lab10-app-devops-info-python   5/5     5            5           7m40s  devops-info-python   devops-info-python:lab9   app.kubernetes.io/instance=lab10-app,app.kubernetes.io/name=devops-info-python
service/lab10-app-devops-info-python           LoadBalancer 10.96.192.136 <pending> 80:30081/TCP 7m40s app.kubernetes.io/instance=lab10-app,app.kubernetes.io/name=devops-info-python
```

Uninstall operation command and output:

```bash
helm uninstall lab10-app
```

```text
release "lab10-app" uninstalled
```

(Used as cleanup before re-install in this evidence run.)

Helm history command and output:

```bash
helm history lab10-app
```

```text
REVISION UPDATED                  STATUS     CHART                    APP VERSION DESCRIPTION
1        Wed Apr  1 10:31:59 2026 superseded devops-info-python-0.1.0 lab9       Install complete
2        Wed Apr  1 10:34:07 2026 superseded devops-info-python-0.1.0 lab9       Upgrade complete
3        Wed Apr  1 10:36:17 2026 superseded devops-info-python-0.1.0 lab9       Rollback to 1
4        Wed Apr  1 10:38:10 2026 superseded devops-info-python-0.1.0 lab9       Rollback to 2
5        Wed Apr  1 10:39:46 2026 deployed   devops-info-python-0.1.0 lab9       Rollback to 2
```

## 6. Testing & Validation

Lint command and output:

```bash
helm lint labs_solution/lab10/k8s/devops-info-python
```

```text
==> Linting labs_solution/lab10/k8s/devops-info-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Template verification commands and outputs:

```bash
helm template lab10-dev labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-dev.yaml
helm template lab10-prod labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-prod.yaml
```

```text
(dev key lines)
14:  type: NodePort
23:      nodePort: 30081
38:  replicas: 1
76:          livenessProbe:
84:          readinessProbe:
105:    "helm.sh/hook": post-install
141:    "helm.sh/hook": pre-install

(prod key lines)
14:  type: LoadBalancer
37:  replicas: 5
75:          livenessProbe:
83:          readinessProbe:
104:    "helm.sh/hook": post-install
140:    "helm.sh/hook": pre-install
```

Dry-run validation commands and outputs:

```bash
helm install --dry-run=client --debug lab10-dev-check labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-dev.yaml
helm install --dry-run=client --debug lab10-prod-check labs_solution/lab10/k8s/devops-info-python -f labs_solution/lab10/k8s/devops-info-python/values-prod.yaml
```

```text
(dev key lines)
7:STATUS: pending-install
109:    "helm.sh/hook": post-install
145:    "helm.sh/hook": pre-install
206:  replicas: 1

(prod key lines)
7:STATUS: pending-install
108:    "helm.sh/hook": post-install
144:    "helm.sh/hook": pre-install
204:  replicas: 5
```

Application accessibility commands and outputs:

```bash
kubectl port-forward svc/lab10-app-devops-info-python 18080:80
curl http://127.0.0.1:18080/health
curl http://127.0.0.1:18080/
```

```text
{"status":"healthy","timestamp":"2026-04-01T07:35:14.680317+00:00","uptime_seconds":61}

{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},...}
```

Both environments tested conclusion:
- Dev tested via template, dry-run, and real install (`replicas=1`, `NodePort`).
- Prod tested via template, dry-run, and real upgrade (`replicas=5`, `LoadBalancer`).
- Health checks are active and remained functional throughout deployment.
- Helper templates are implemented and used for naming/labels in manifests.
