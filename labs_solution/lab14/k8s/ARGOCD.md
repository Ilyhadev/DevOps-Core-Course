# Lab 13 - GitOps with ArgoCD

This file documents only the parts required by `labs/lab13.md`: ArgoCD setup, application deployment, multi-environment deployment, and self-healing checks. All outputs below are real terminal outputs collected during the lab run.

## Task 1 - ArgoCD Installation & Access

ArgoCD was installed with Helm into a dedicated `argocd` namespace.

```bash
$ helm repo add argo https://argoproj.github.io/argo-helm
"argo" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "argo" chart repository

$ kubectl create namespace argocd
namespace/argocd created

$ helm install argocd argo/argo-cd --namespace argocd
NAME: argocd
LAST DEPLOYED: Wed Apr 22 10:50:53 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

ArgoCD components became ready:

```bash
$ kubectl get pods -n argocd
NAME                                                 READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                      1/1     Running   0          2m22s
argocd-applicationset-controller-684c6b8f56-wg4zf   1/1     Running   0          2m22s
argocd-dex-server-799c76595f-tlkd4                   1/1     Running   0          2m22s
argocd-notifications-controller-66b84df6b4-v4rrp     1/1     Running   0          2m22s
argocd-redis-84889d765c-zpz9g                        1/1     Running   0          2m22s
argocd-repo-server-6d87744868-95lcb                  1/1     Running   0          2m22s
argocd-server-796cffdfdd-2gws7                       1/1     Running   0          2m22s
```

UI access and initial password retrieval:

```bash
$ kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
[REDACTED]

$ kubectl port-forward svc/argocd-server -n argocd 8080:443
Forwarding from 127.0.0.1:8080 -> 8080
Forwarding from [::1]:8080 -> 8080
```

## Task 2 - Application Deployment

Three ArgoCD `Application` manifests were prepared:

- Base app: [application.yaml](/home/ilia/Desktop/vsCode/DevOps/DevOps-Core-Course/labs_solution/lab13/k8s/argocd/application.yaml)
- Dev app: [application-dev.yaml](/home/ilia/Desktop/vsCode/DevOps/DevOps-Core-Course/labs_solution/lab13/k8s/argocd/application-dev.yaml)
- Prod app: [application-prod.yaml](/home/ilia/Desktop/vsCode/DevOps/DevOps-Core-Course/labs_solution/lab13/k8s/argocd/application-prod.yaml)

Current ArgoCD application status:

```bash
$ kubectl get applications -n argocd
NAME              SYNC STATUS   HEALTH STATUS
python-app        Synced        Healthy
python-app-dev    Synced        Healthy
python-app-prod   Synced        Progressing
```

Meaning of the current state:

- `python-app` is deployed to `default` and fully healthy.
- `python-app-dev` is deployed to `dev` and fully healthy.
- `python-app-prod` is deployed to `prod` and synced, but shows `Progressing` because the service type is `LoadBalancer` and kind keeps `EXTERNAL-IP` as `<pending>`.

## Task 3 - Multi-Environment Deployment

Environment namespaces:

```bash
$ kubectl get ns dev prod
NAME   STATUS   AGE
dev    Active   43m
prod   Active   42m
```

Deployment state across namespaces:

```bash
$ kubectl get deployments -A | grep python-app
default              python-app-devops-info-python        3/3     3            3           18m
dev                  python-app-dev-devops-info-python    1/1     1            1           10m
prod                 python-app-prod-devops-info-python   5/5     5            5           18m
```

Running pods:

```bash
$ kubectl get pods -A | grep python-app
default              python-app-devops-info-python-8d68b757d-2xzbv          1/1     Running     0   18m
default              python-app-devops-info-python-8d68b757d-g55xq          1/1     Running     0   18m
default              python-app-devops-info-python-8d68b757d-tj5jh          1/1     Running     0   18m
dev                  python-app-dev-devops-info-python-5498c76596-kmvmk     1/1     Running     0   10m
prod                 python-app-prod-devops-info-python-6fff66c7f9-fptlm    1/1     Running     0   18m
prod                 python-app-prod-devops-info-python-6fff66c7f9-g6cbn    1/1     Running     0   18m
prod                 python-app-prod-devops-info-python-6fff66c7f9-g6qxh    1/1     Running     0   18m
prod                 python-app-prod-devops-info-python-6fff66c7f9-h5q79    1/1     Running     0   18m
prod                 python-app-prod-devops-info-python-6fff66c7f9-mdctz    1/1     Running     0   18m
```

Services show environment-specific differences:

```bash
$ kubectl get svc -A | grep python-app
default   python-app-devops-info-python        NodePort       10.96.31.247    <none>      80:30081/TCP   18m
dev       python-app-dev-devops-info-python    NodePort       10.96.120.93    <none>      80:30082/TCP   4m54s
prod      python-app-prod-devops-info-python   LoadBalancer   10.96.71.63     <pending>   80:32536/TCP   18m
```

Notes:

- `dev` uses auto-sync with `prune` and `selfHeal`.
- `prod` stays manual.
- `dev` uses `NodePort 30082` to avoid collision with the base app on `30081`.
- `prod` remains `Progressing` because kind does not provision a real external load balancer IP.

## Task 4 - Self-Healing & Drift Checks

### 4.1 Manual Scale Drift

Initial state:

```bash
$ kubectl get deployment python-app-dev-devops-info-python -n dev -o jsonpath='{.spec.replicas}{"\n"}'
1

$ kubectl get application python-app-dev -n argocd -o jsonpath='{.status.sync.status}{"\n"}'
Synced
```

Manual drift:

```bash
$ kubectl scale deployment python-app-dev-devops-info-python -n dev --replicas=5
deployment.apps/python-app-dev-devops-info-python scaled
```

Deployment events show the manual scale and the automatic rollback to Git state:

```bash
$ kubectl describe deployment python-app-dev-devops-info-python -n dev
...
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  79s   deployment-controller  Scaled up replica set python-app-dev-devops-info-python-5498c76596 to 5 from 1
  Normal  ScalingReplicaSet  74s   deployment-controller  Scaled down replica set python-app-dev-devops-info-python-5498c76596 to 1 from 5
...
```

This demonstrates ArgoCD self-healing of configuration drift in the `dev` environment.

### 4.2 Pod Deletion Test

Pod before deletion:

```bash
$ kubectl get pods -n dev -l app.kubernetes.io/name=devops-info-python -o custom-columns=NAME:.metadata.name,STATUS:.status.phase --no-headers
python-app-dev-devops-info-python-7b9747f456-6b6pm   Pending
python-app-dev-devops-info-python-7b9747f456-nw24x   Running
```

Manual pod deletion:

```bash
$ kubectl delete pod -n dev -l app.kubernetes.io/name=devops-info-python
pod "python-app-dev-devops-info-python-7b9747f456-nw24x" deleted from dev namespace
```

State after recreation:

```bash
$ kubectl get pods -n dev -l app.kubernetes.io/name=devops-info-python -o wide
NAME                                                 READY   STATUS    RESTARTS   AGE   IP            NODE                  NOMINATED NODE   READINESS GATES
python-app-dev-devops-info-python-7b9747f456-6b6pm   1/1     Running   0          82s   10.244.0.39   lab13-control-plane   <none>           <none>

$ kubectl get deployment python-app-dev-devops-info-python -n dev -o jsonpath='{.spec.replicas} {.status.readyReplicas}{"\n"}'
1 1

$ kubectl get application python-app-dev -n argocd -o jsonpath='{.status.sync.status} {.status.health.status}{"\n"}'
Synced Healthy
```

Recent events confirm pod recreation:

```bash
$ kubectl get events -n dev --sort-by=.lastTimestamp | tail -n 20
...
78s   Normal  SuccessfulCreate  replicaset/python-app-dev-devops-info-python-7b9747f456  Created pod: python-app-dev-devops-info-python-7b9747f456-6b6pm
78s   Normal  Killing           pod/python-app-dev-devops-info-python-7b9747f456-nw24x   Stopping container devops-info-python
75s   Normal  Started           pod/python-app-dev-devops-info-python-7b9747f456-6b6pm   Started container devops-info-python
...
```

This demonstrates Kubernetes self-healing: ReplicaSet recreated the deleted pod while ArgoCD stayed `Synced Healthy`.

### 4.3 Manual Template Drift

I also patched the `dev` deployment template with a temporary label to produce a rollout. The deployment output showed the patched label and ReplicaSet rotation:

```bash
$ kubectl describe deployment python-app-dev-devops-info-python -n dev
...
Pod Template:
  Labels:  app.kubernetes.io/component=web
           app.kubernetes.io/instance=python-app-dev
           app.kubernetes.io/name=devops-info-python
           manual-test=true
...
Events:
  Normal  ScalingReplicaSet  50s  deployment-controller  Scaled up replica set python-app-dev-devops-info-python-85b95965f9 to 1
  Normal  ScalingReplicaSet  30s  deployment-controller  Scaled down replica set python-app-dev-devops-info-python-85b95965f9 to 0 from 1
  Normal  ScalingReplicaSet  30s  deployment-controller  Scaled up replica set python-app-dev-devops-info-python-7b9747f456 to 1 from 0
```

After capturing this evidence, the temporary label was removed and the deployment was returned to a clean state.

#### Bonus note: ApplicationSet manifest was prepared in applicationset.yaml

## Note

The lab requirements for Task 1-4 are covered with command evidence above. The only non-`Healthy` application state is `python-app-prod = Progressing`, which is expected in kind because `LoadBalancer` services stay with `EXTERNAL-IP <pending>`.
