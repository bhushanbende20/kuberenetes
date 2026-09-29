# es-fleet — Elasticsearch on Kubernetes with ECK + FluxCD

GitOps repository for managing multiple Elasticsearch clusters across **dev / stage / prod**
using the [Elastic Cloud on Kubernetes (ECK)](https://www.elastic.co/guide/en/cloud-on-k8s/current/index.html)
operator and [FluxCD](https://fluxcd.io/) for continuous reconciliation.

---

## Repository layout

```
es-fleet/
├── flux-system/                        # Flux bootstrap manifests (generated + this sync)
│   ├── gotk-sync.yaml                  # GitRepository + root Kustomization
│   └── kustomization.yaml
│
├── clusters/                           # One folder per cluster; Flux points here
│   ├── dev/
│   │   ├── kustomization.yaml          # entrypoint for flux-system
│   │   └── kustomizations.yaml         # Flux Kustomization CRs (eck-operator + es-dev)
│   ├── stage/
│   └── prod/
│
└── infrastructure/
    ├── eck-operator/                   # ECK Helm operator (HelmRepository + HelmRelease)
    │   ├── namespace.yaml
    │   ├── helmrepository.yaml
    │   ├── helmrelease.yaml
    │   └── kustomization.yaml
    │
    └── elasticsearch/
        ├── base/                       # Base ECK Elasticsearch CRD template
        │   ├── namespace.yaml
        │   ├── elasticsearch.yaml
        │   └── kustomization.yaml
        └── overlays/
            ├── dev/                    # 1-node, small resources, 2 clusters
            │   ├── kustomization.yaml
            │   └── es-cluster-dev.yaml
            ├── stage/                  # 2-node, medium resources, 2 clusters
            │   ├── kustomization.yaml
            │   └── es-cluster-stage.yaml
            └── prod/                   # HA: dedicated master/data/ingest, 2 clusters
                ├── kustomization.yaml
                └── es-cluster-prod-search.yaml
```

---

## Prerequisites

| Tool | Min version |
|------|------------|
| `flux` CLI | v2.3+ |
| `kubectl` | v1.28+ |
| `kustomize` | v5+ |
| Kubernetes cluster | v1.27+ |
| GitHub / GitLab repo | — |

---

## Bootstrap (first time)

### 1. Export credentials

```bash
# needs repo read/write + admin:org #EXPORTGITHUBTOKENGERE
export GITHUB_USER=bhushanbende20
export GITHUB_REPO=kuberenetes
           # this repo name
```

### 2. Bootstrap Flux into the dev cluster

```bash
flux bootstrap github \
  --owner="${GITHUB_USER}" \
  --repository="${GITHUB_REPO}" \
  --branch=main \
  --path=eck_flux/es-fleet/clusters/dev \
  --personal \
  --components-extra=image-reflector-controller,image-automation-controller
```

Flux will:
1. Create the `flux-system` namespace and install all Flux controllers.
2. Generate an SSH deploy key and add it to your GitHub repo.
3. Commit `flux-system/gotk-components.yaml` and `gotk-sync.yaml` to `main`.
4. Begin reconciling `clusters/dev/` — which installs ECK operator first, then ES clusters.

### 3. Bootstrap stage / prod (separate clusters)

Switch `kubeconfig` context to the stage cluster, then run:

```bash
flux bootstrap github \
  --owner="${GITHUB_USER}" \
  --repository="${GITHUB_REPO}" \
  --branch=main \
  --path=clusters/stage \
  --personal
```

And repeat with `--path=clusters/prod` for production.

---

## Verify reconciliation

```bash
# Watch all Flux objects
flux get all -A

# Check ECK operator
kubectl get pods -n elastic-system

# Check ES clusters (dev)
kubectl get elasticsearch -n elasticsearch-dev

# Get elastic user password for a cluster
kubectl get secret es-cluster-dev-es-elastic-user \
  -n elasticsearch-dev \
  -o jsonpath='{.data.elastic}' | base64 -d
```

---

## Adding a new Elasticsearch cluster

To spin up an additional ES cluster inside an existing overlay (e.g. dev):

1. Create a new manifest in the overlay dir:

```bash
cp infrastructure/elasticsearch/overlays/dev/es-cluster-dev.yaml \
   infrastructure/elasticsearch/overlays/dev/es-cluster-logs.yaml
```

2. Edit `es-cluster-logs.yaml` — change `metadata.name` and tune resources.

3. Add it to the overlay `kustomization.yaml`:

```yaml
resources:
  - ../../base
  - es-cluster-dev.yaml
  - es-cluster-logs.yaml    # ← add this line
```

4. Commit and push — Flux reconciles within `interval` (default 5m).

---

## Cluster sizing reference

| Env   | Nodes | Memory/node | Storage/node | Node roles            |
|-------|-------|-------------|--------------|------------------------|
| dev   | 1     | 1 Gi        | 5 Gi         | master + data + ingest |
| stage | 2     | 2 Gi        | 20 Gi        | master + data + ingest |
| prod  | 3+3+2 | 4–16 Gi     | 10–500 Gi    | dedicated per role     |

---

## Upgrading ECK operator version

Edit `infrastructure/eck-operator/helmrelease.yaml`:

```yaml
spec:
  chart:
    spec:
      version: "2.14.*"   # bump here
```

Commit → Flux applies the Helm upgrade automatically.

## Upgrading Elasticsearch version

Edit the relevant overlay patch or cluster manifest:

```yaml
- op: replace
  path: /spec/version
  value: "8.14.0"
```

ECK performs a rolling upgrade respecting shard allocation and cluster health.

---

## Security notes

- ECK enables TLS on HTTP and transport by default with self-signed certs.
- Bring your own cert by adding a `tls.certificate` secret and referencing it in `spec.http.tls`.
- The `elastic` superuser password is stored as a Kubernetes Secret; retrieve with `kubectl get secret`.
- For production, consider enabling [Elasticsearch keystore secrets](https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-es-secure-settings.html).
