# Lab 9 - Kubernetes Fundamentals

## Architecture Overview

Local cluster:

- Tool: `kind`
- Context: `kind-devops-lab9`
- Node count: 1 control-plane node
- Kubernetes version: `v1.30.0`

Required app architecture:

- Deployment: `devops-info-python`
- Service: `devops-info-python` (`NodePort`, `80 -> 8080`, `nodePort: 30080`)
- Labels/selectors: `app=devops-info-python`
- Health checks: liveness/readiness on `/health`
- Resources (per Pod): requests `100m/128Mi`, limits `250m/256Mi`

Networking flow:

`Client -> NodePort/port-forward -> Service -> Pods`

## Manifest Files

- `deployment.yml`: main Python deployment with 3 replicas, rolling strategy, probes, resources.
- `service.yml`: NodePort service exposing the deployment.
- `deployment-canary.yml`: update manifest used for rolling update demo (5 replicas + config change).
- `deployment-app2.yml` (bonus): second app deployment (Go).
- `service-app2.yml` (bonus): second app service.
- `ingress.yml` (bonus): path routing + TLS configuration.

## Deployment Evidence

### Task 1 - Local Kubernetes Setup

Cluster info and node status:

```text
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:44921
CoreDNS is running at https://127.0.0.1:44921/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

$ kubectl get nodes -o wide
NAME                        STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION      CONTAINER-RUNTIME
devops-lab9-control-plane   Ready    control-plane   95m   v1.30.0   172.18.0.2    <none>        Debian GNU/Linux 12 (bookworm)   6.14.0-37-generic   containerd://1.7.15
```

Tool choice rationale:

- `kind` was chosen because it is lightweight, fast for local iteration, and does not require cloud resources.

### Task 2 - Application Deployment

`[EVIDENCE REQUIRED]` Initial deployment + service apply:

```text
$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-python created

$ kubectl apply -f k8s/service.yml
service/devops-info-python created
```

`[EVIDENCE REQUIRED]` Baseline deployment state before scaling (3 replicas):

```text
$ kubectl get deployments -l app=devops-info-python
NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-python   3/3     3            3           11m

$ kubectl get pods -l app=devops-info-python -o wide
NAME                                  READY   STATUS    RESTARTS   AGE    IP            NODE                        NOMINATED NODE   READINESS GATES
devops-info-python-85d9f498f9-445vv   1/1     Running   0          93s    10.244.0.10   devops-lab9-control-plane   <none>           <none>
devops-info-python-85d9f498f9-87rhp   1/1     Running   0          104s   10.244.0.9    devops-lab9-control-plane   <none>           <none>
devops-info-python-85d9f498f9-x7pt5   1/1     Running   0          83s    10.244.0.11   devops-lab9-control-plane   <none>           <none>
```

`[EVIDENCE REQUIRED]` Deployment details with required best practices (before scaling):

```text
$ kubectl describe deployment devops-info-python
Name:                   devops-info-python
Namespace:              default
Annotations:            deployment.kubernetes.io/revision: 3
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
...
Image:      devops-info-python:lab9
Limits:
  cpu:     250m
  memory:  256Mi
Requests:
  cpu:      100m
  memory:   128Mi
Liveness:   http-get http://:http/health delay=15s timeout=2s period=10s #success=1 #failure=3
Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s #success=1 #failure=3
```

### Task 3 - Service Configuration

`[EVIDENCE REQUIRED]` Service and app Pods (baseline stage):

```text
$ kubectl get pods,svc -l app=devops-info-python -o wide
NAME                                  READY   STATUS    RESTARTS   AGE    IP            NODE                        NOMINATED NODE   READINESS GATES
pod/devops-info-python-85d9f498f9-445vv   1/1     Running   0          93s    10.244.0.10   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-87rhp   1/1     Running   0          104s   10.244.0.9    devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-x7pt5   1/1     Running   0          83s    10.244.0.11   devops-lab9-control-plane   <none>           <none>

NAME                         TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-python   NodePort   10.96.75.147   <none>        80:30080/TCP   11m   app=devops-info-python

$ kubectl get endpoints devops-info-python -o wide
NAME                 ENDPOINTS                                                        AGE
devops-info-python   10.244.0.19:8080,10.244.0.20:8080,10.244.0.21:8080 + 2 more...   79m
```

Note: endpoint snapshot above was captured later in the session after scaling, which is why it shows `+ 2 more`.

`[EVIDENCE REQUIRED]` Connectivity check via service port-forward:

```text
$ kubectl port-forward service/devops-info-python 18080:80

$ curl http://127.0.0.1:18080/health
{"status":"healthy","timestamp":"2026-03-23T13:59:10.902232+00:00","uptime_seconds":694}

$ curl http://127.0.0.1:18080/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-03-23T13:59:10.921235+00:00","timezone":"UTC","uptime_human":"0 hours, 11 minutes","uptime_seconds":694},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},...}
```

### Task 4 - Scaling and Updates

 Scaling to 5 replicas:

```text
$ kubectl scale deployment/devops-info-python --replicas=5
deployment.apps/devops-info-python scaled

$ kubectl rollout status deployment/devops-info-python
deployment "devops-info-python" successfully rolled out

$ kubectl get deployment devops-info-python
NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-python   5/5     5            5           17m
```

 Rolling update:

```text
$ kubectl apply -f k8s/deployment-canary.yml
deployment.apps/devops-info-python configured

$ kubectl rollout status deployment/devops-info-python
deployment "devops-info-python" successfully rolled out

$ kubectl rollout history deployment/devops-info-python
deployment.apps/devops-info-python
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
4         <none>

$ kubectl get rs -l app=devops-info-python
NAME                            DESIRED   CURRENT   READY   AGE
devops-info-python-55fbb48db6   0         0         0       8m33s
devops-info-python-6975946b68   0         0         0       18m
devops-info-python-85d9f498f9   0         0         0       8m33s
devops-info-python-88dd57c5f    5         5         5       53s
```

 Rollback:

```text
$ kubectl rollout undo deployment/devops-info-python
deployment.apps/devops-info-python rolled back

$ kubectl rollout status deployment/devops-info-python
deployment "devops-info-python" successfully rolled out

$ kubectl rollout history deployment/devops-info-python
deployment.apps/devops-info-python
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
4         <none>
5         <none>

$ kubectl get rs -l app=devops-info-python
NAME                            DESIRED   CURRENT   READY   AGE
devops-info-python-55fbb48db6   0         0         0       59m
devops-info-python-6975946b68   0         0         0       69m
devops-info-python-85d9f498f9   5         5         5       59m
devops-info-python-88dd57c5f    0         0         0       51m
```

## Task 5 - Required Evidence Snapshots

 `kubectl get all -o wide`:

```text
NAME                                      READY   STATUS    RESTARTS   AGE   IP            NODE                        NOMINATED NODE   READINESS GATES
pod/devops-info-python-85d9f498f9-2n2r7   1/1     Running   0          10m   10.244.0.22   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-9qzzd   1/1     Running   0          11m   10.244.0.19   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-f2xvw   1/1     Running   0          10m   10.244.0.21   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-f778f   1/1     Running   0          10m   10.244.0.23   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-tcq57   1/1     Running   0          10m   10.244.0.20   devops-lab9-control-plane   <none>           <none>

NAME                         TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-python   NodePort    10.96.75.147   <none>        80:30080/TCP   79m   app=devops-info-python
service/kubernetes           ClusterIP   10.96.0.1      <none>        443/TCP        94m   <none>

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS           IMAGES                    SELECTOR
deployment.apps/devops-info-python   5/5     5            5           79m   devops-info-python   devops-info-python:lab9   app=devops-info-python
```

 `kubectl get pods,svc -o wide` (app-specific):

```text
NAME                                      READY   STATUS    RESTARTS   AGE   IP            NODE                        NOMINATED NODE   READINESS GATES
pod/devops-info-python-85d9f498f9-2n2r7   1/1     Running   0          10m   10.244.0.22   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-9qzzd   1/1     Running   0          11m   10.244.0.19   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-f2xvw   1/1     Running   0          11m   10.244.0.21   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-f778f   1/1     Running   0          10m   10.244.0.23   devops-lab9-control-plane   <none>           <none>
pod/devops-info-python-85d9f498f9-tcq57   1/1     Running   0          11m   10.244.0.20   devops-lab9-control-plane   <none>           <none>

NAME                         TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-python   NodePort   10.96.75.147   <none>        80:30080/TCP   79m   app=devops-info-python
```

## Operations Performed

Commands used:

```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl scale deployment/devops-info-python --replicas=5
kubectl apply -f k8s/deployment-canary.yml
kubectl rollout undo deployment/devops-info-python
```

Service access method:

- `kubectl port-forward service/devops-info-python 18080:80`
- `curl` requests to `/health` and `/`

## Production Considerations

Health checks:

- Using `/health` for readiness/liveness provides fast failover and automatic restart/removal from traffic.

Resource limits rationale:

- Requests guarantee scheduling on a small local cluster.
- Limits prevent runaway CPU/memory usage and protect cluster stability.

Improvements for production:

- Use immutable versioned registry images per release.
- Split readiness and liveness endpoints.
- Add HPA, PDB, namespace isolation, and RBAC service accounts.
- Add centralized metrics/logs with alerting (Prometheus + Grafana + Loki).

Monitoring and observability strategy:

- Scrape `/metrics` endpoint.
- Alert on probe failures, restart spikes, 5xx error rate, and latency SLO breaches.

## Challenges and Solutions

Issue:

- Pods initially failed with `ImagePullBackOff` and Docker Hub `TLS handshake timeout`.

Debug method:

- `kubectl describe deployment` and `kubectl describe pods` events.

Fix:

- Built local images and loaded them into kind:

```bash
docker build -t devops-info-python:lab9 labs_solution/lab1/app_python
docker build -t devops-info-go:lab9 labs_solution/lab1/app_go
kind load docker-image devops-info-python:lab9 --name devops-lab9
kind load docker-image devops-info-go:lab9 --name devops-lab9
```

Lesson learned:

- For local/offline labs, preloaded local images are more reliable than external pulls.

## Screenshot Index

Screenshots used from `labs_solution/lab9/docs/screenshots`:

- `lab8_healthy_cluster.png` (Task 1 evidence)
- `lab8_3_replicas.png` (Task 2 baseline replicas)
- `8lab_3_pods_details.png` (Task 2/3 pod + service detail)
- `lab8_deployment_details_before_scailing.png` (Deployment describe details)
- `lab8_app_work_before_scailing.png` (Service connectivity proof)
- `lab8_after_scailing.png` (Scaling to 5 replicas)
- `lab8_rollout_in_action.png` (Rolling update in progress)
- `lab8_rollout_after_scailing.png` (Rollout/ReplicaSet result)

## Bonus - Ingress with TLS (Optional)

Prepared manifests:

- `deployment-app2.yml`
- `service-app2.yml`
- `ingress.yml`

If bonus is executed, add these evidence outputs:

```bash
kubectl apply -f k8s/deployment-app2.yml
kubectl apply -f k8s/service-app2.yml
kubectl apply -f k8s/ingress.yml
kubectl get ingress
curl -k https://local.example.com/app1
curl -k https://local.example.com/app2
```
