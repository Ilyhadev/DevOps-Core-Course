# Lab 16 - Kubernetes Monitoring & Init Containers

This document captures Lab 16 implementation:
- kube-prometheus-stack installation
- Grafana/Alertmanager access workflow
- init container patterns (download + wait-for-service)

Command outputs are stored in `k8s/temp.txt`.

## 1) Stack components (in my own words)

- **Prometheus Operator**: Kubernetes controller that manages Prometheus/Alertmanager resources via CRDs and keeps configs aligned.
- **Prometheus**: collects and stores time-series metrics from cluster and workloads.
- **Alertmanager**: receives alerts from Prometheus, groups/deduplicates/routes them.
- **Grafana**: visualization layer for metrics dashboards.
- **kube-state-metrics**: exposes Kubernetes object state metrics (deployments, pods, PVCs, etc.).
- **node-exporter**: exposes host/node-level metrics (CPU, memory, filesystem, network).

## 2) Installation evidence

Installed via Helm into `monitoring` namespace:

```bash
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

Evidence (`kubectl get pods,svc -n monitoring`) is saved in `k8s/temp.txt` and includes running:
- `monitoring-kube-prometheus-operator`
- `prometheus-monitoring-kube-prometheus-prometheus-0`
- `alertmanager-monitoring-kube-prometheus-alertmanager-0`
- `monitoring-grafana`
- `monitoring-kube-state-metrics`
- `monitoring-prometheus-node-exporter`

## 3) Grafana dashboard exploration (questions)

Use:

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

Default Grafana user is `admin`.
Password retrieved in `k8s/temp.txt` from:

```bash
kubectl -n monitoring get secret monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d
```

Dashboards to use:
- Kubernetes / Compute Resources / Namespace (Pods)
- Kubernetes / Compute Resources / Pod
- Node Exporter / Nodes
- Kubernetes / Kubelet

Answer these in your final report with screenshots:
1. CPU/memory usage of StatefulSet pods
2. Most/least CPU pods in default namespace
3. Node memory usage (% and MB), CPU cores
4. Number of pods/containers managed by kubelet
5. Network traffic for pods in default namespace
6. Active alerts from Alertmanager UI

### Dashboard answers from this run

1. **Pod resources (StatefulSet)**
   - Dashboard evidence: `screenshots/lab16_graph_8_default.png` and `screenshots/lab16_graph_7_namespace_default.png`
   - For namespace `default`, pod CPU usage values are around `0.0011-0.00123` cores for the shown `devops-info-python-*` pods.
   - The namespace dashboard also shows memory utilization for `default` around `41.0%` (from requests) and `20.5%` (from limits) at capture time.

2. **Most/least CPU in `default` namespace**
   - Evidence: `screenshots/lab16_graph_7_namespace_default.png` (CPU Quota table for `default`).
   - At capture time:
     - Highest shown CPU usage: `devops-info-python-67d4d45f85-6kvmg` (`~0.00123`)
     - Lowest shown CPU usage: `devops-info-python-67d4d45f85-7qflr` (`~0.00115`)

3. **Node metrics (memory %/MB and CPU cores)**
   - Evidence: `screenshots/lab16_graph_3.png`
   - Node memory gauge shows about `52.7%`.
   - CPU panel includes per-core lines, indicating multi-core node metrics are collected and visible.

4. **Kubelet managed pods/containers**
   - Evidence: `screenshots/lab16_graph_4.png`
   - `Running Pods: 26`
   - `Running Containers: 53`

5. **Network traffic for pods**
   - Evidence: `screenshots/lab16_graph_6.png`
   - Current receive/transmit bandwidth and packet rates are shown in the network panels (Receive/Transmit Bandwidth and packet rate charts).

6. **Active alerts**
   - Evidence: `screenshots/lab16_alerts.png`
   - Alertmanager shows active groups, including a `namespace="kube-system"` group with `5 alerts` at capture time.

## 4) Init containers implementation

Implemented in `k8s/devops-info-python/templates/statefulset.yaml` with values in `k8s/devops-info-python/values.yaml`:

1. **wait-for-service init container**
   - Uses `nslookup kubernetes.default.svc.cluster.local` loop
   - Main container starts only after dependency resolves

2. **init-download init container**
   - Uses `wget -O /work-dir/index.html https://example.com`
   - Shares data via `emptyDir` volume
   - Main container mounts the same volume at `/init-data`

Verification evidence in `k8s/temp.txt`:
- init logs from both init containers
- file exists and is readable from main container:
  - `/init-data/index.html`

## 5) Bonus - custom metrics / ServiceMonitor

App already exposes `/metrics` endpoint in Lab 12+ code.
ServiceMonitor can be added next to scrape app metrics from Prometheus if bonus is required in final grading.

## Screenshot index

- `screenshots/lab16_graph_1.png` - Kubernetes compute overview
- `screenshots/lab16_graph_2.png` - CoreDNS dashboard view
- `screenshots/lab16_graph_3.png` - Node Exporter / Nodes
- `screenshots/lab16_graph_4.png` - Kubernetes / Kubelet
- `screenshots/lab16_graph_5.png` - Namespace pods view
- `screenshots/lab16_graph_6.png` - Pod network traffic view
- `screenshots/lab16_graph_7_namespace_default.png` - Namespace `default` CPU table
- `screenshots/lab16_graph_8_default.png` - Pod compute details (`default`)
- `screenshots/lab16_alerts.png` - Alertmanager active alerts

