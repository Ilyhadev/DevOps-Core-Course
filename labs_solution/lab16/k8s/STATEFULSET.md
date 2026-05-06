# Lab 15 - StatefulSet & Persistent Storage

This document covers Lab 15 requirements using the Helm chart in `k8s/devops-info-python` converted from Deployment to StatefulSet.

Command evidence was captured to `k8s/temp.txt`.

## 1) StatefulSet overview and comparison

StatefulSets are used when pods need:
- stable pod names (`...-0`, `...-1`, `...-2`)
- stable network identities (DNS per pod)
- stable per-pod persistent storage
- ordered rollout/scaling behavior

Deployment vs StatefulSet:
- **Pod naming**: Deployment pods get random suffixes; StatefulSet pods have stable ordinals.
- **Storage**: Deployment commonly uses shared/static PVC; StatefulSet uses `volumeClaimTemplates` to create one PVC per pod.
- **Identity**: StatefulSet + headless Service gives DNS names per pod.
- **Update behavior**: StatefulSet supports ordered updates, partitioned rolling updates, and `OnDelete`.

Typical stateful workloads: PostgreSQL/MySQL, Kafka, Redis clusters, Elasticsearch, etc.

## 2) Resource verification

Converted resources:
- `templates/statefulset.yaml` (replaces deployment)
- `templates/service-headless.yaml` (`clusterIP: None`)
- retained `templates/service.yaml` for external access
- removed old standalone `templates/pvc.yaml` in favor of `volumeClaimTemplates`

Verification output (from `temp.txt`):
- `kubectl get po,sts,svc,pvc -n lab15 -o wide`
- StatefulSet pods are `lab15-app-devops-info-python-0/1/2`
- Headless service exists: `lab15-app-devops-info-python-headless`
- 3 PVCs were auto-created:
  - `data-lab15-app-devops-info-python-0`
  - `data-lab15-app-devops-info-python-1`
  - `data-lab15-app-devops-info-python-2`

## 3) Network identity and DNS

DNS test was executed from pod `...-0`:
- resolved
  - `lab15-app-devops-info-python-1.lab15-app-devops-info-python-headless.lab15.svc.cluster.local`
  - `lab15-app-devops-info-python-2.lab15-app-devops-info-python-headless.lab15.svc.cluster.local`

Result in `temp.txt` confirms each pod resolves directly by ordinal-based DNS name.

## 4) Per-pod storage isolation

Per-pod checks were run by hitting each pod locally through `kubectl exec`:
- pod `-0`: visits became `2`
- pod `-1`: visits became `1`
- pod `-2`: visits remained `0`

This demonstrates isolated storage files mounted from separate PVCs.

## 5) Persistence after pod deletion

Persistence test on pod `-0`:
- before delete: `/data/visits = 2`
- pod `-0` deleted
- StatefulSet recreated pod `-0`
- after restart: `/data/visits = 2`

This confirms data survived pod restart because the same PVC was reattached.

## Bonus: update strategies

### Partitioned RollingUpdate

Configured with:
- `statefulset.updateStrategy.type: RollingUpdate`
- `statefulset.updateStrategy.rollingUpdate.partition: 2`

Observed result:
- only pod `-2` moved to new revision hash first
- pods `-0` and `-1` stayed on previous revision hash

### OnDelete strategy

Configured with:
- `statefulset.updateStrategy.type: OnDelete`

Observed result:
- StatefulSet strategy reported `OnDelete`
- pods did not change revision automatically after chart update
- after manually deleting pod `-2`, it recreated on the new revision hash

## Files changed

- `k8s/devops-info-python/templates/statefulset.yaml`
- `k8s/devops-info-python/templates/service-headless.yaml`
- `k8s/devops-info-python/templates/service.yaml` (kept external service)
- `k8s/devops-info-python/values.yaml`
- `k8s/devops-info-python/values-partition.yaml`
- `k8s/devops-info-python/values-ondelete.yaml`
- `k8s/temp.txt` (command evidence)

