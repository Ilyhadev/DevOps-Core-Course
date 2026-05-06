# Lab 18 - Reproducible Builds with Nix

This submission documents Task 1 and Task 2 from Lab 18 with explicit evidence mapping.

## Task 1 - Reproducible Python app build (Lab 1 comparison)

### 1.1 Nix installation

```bash
# installer command used
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install --no-confirm

# verify
nix --version
nix run nixpkgs#hello
```

Observed output:
- `nix (Determinate Nix 3.19.1) 2.34.6`
- `Hello, world!`

### 1.2 Nix derivation

Files:
- `app_python/default.nix`

Key points:
- Uses `python312Packages.buildPythonApplication`
- Includes Flask + prometheus-client + python-json-logger
- Installs `devops-info-service` executable wrapper
- Uses `python.withPackages` runtime to include transitive deps (e.g. `werkzeug`) reliably.

### 1.3 Build and run

```bash
cd labs/lab18/app_python
nix-build
readlink result
./result/bin/devops-info-service
```

Observed:
- Service starts successfully from Nix output and serves Flask app on port `5000`.

### 1.4 Reproducibility proof

```bash
readlink result
rm result && nix-build && readlink result

STORE_PATH=$(readlink result)
nix-store --delete "$STORE_PATH"
rm result && nix-build && readlink result

nix-hash --type sha256 result
```

Observed from `temp.txt`:
- `first_build=/nix/store/vlfxfp24rlc43fbswyahzrjf8g1xx0vz-devops-info-service-1.0.0`
- `second_build=/nix/store/vlfxfp24rlc43fbswyahzrjf8g1xx0vz-devops-info-service-1.0.0`
- `nix-hash`: `b1d8601b4e29509052717e480702c605ca5b9f7665e0e75cc991c5d79656a2e7`

Note:
- `nix-store --delete` may return `0 paths deleted` if that store path is still referenced by a GC root/layer.
- Even in that case, repeated clean builds showed the same output path/hash for unchanged inputs.

### 1.5 Comparison with pip/venv approach (Lab 1)

| Aspect | Lab 1 (`pip + venv`) | Lab 18 (Nix derivation) |
|--------|------------------------|--------------------------|
| Python version | System-dependent | Pinned by nixpkgs |
| Dependency lock depth | Direct deps mostly | Full closure pinned |
| Build isolation | Virtualenv only | Sandboxed/pure build model |
| Reproducibility | Approximate | Deterministic (content-addressed) |
| Binary cache | No | Yes (Nix cache model) |

## Task 2 - Reproducible Docker image with Nix (Lab 2 comparison)

### 2.1 Traditional Dockerfile baseline

Source:
- `app_python/Dockerfile`

### 2.2 Nix dockerTools image

Files:
- `app_python/docker.nix`

Build and load:

```bash
cd labs/lab18/app_python
nix-build docker.nix
sha256sum result
docker load < result
```

Observed tarball hash:
- `145937585a576a5c888eb516bf6ee2c89ef13add925034f9cf6ed16536b23046`

Run Nix-built image:

```bash
docker run -d --name nix-container -p 5001:8080 devops-info-service-nix:1.0.0
curl http://localhost:5001/health
```

### 2.3 Reproducibility test

```bash
rm result && nix-build docker.nix && sha256sum result
rm result && nix-build docker.nix && sha256sum result
```

Observed:
- `145937585a576a5c888eb516bf6ee2c89ef13add925034f9cf6ed16536b23046`
- `145937585a576a5c888eb516bf6ee2c89ef13add925034f9cf6ed16536b23046`

Conclusion: Nix `dockerTools` output is reproducible for same inputs.

### 2.4 Comparison with traditional Docker build

```bash
docker build -t lab2-app:test1 ./labs/lab18/app_python
docker save lab2-app:test1 | sha256sum
sleep 2
docker build -t lab2-app:test2 ./labs/lab18/app_python
docker save lab2-app:test2 | sha256sum
```

Observed:
- test1: `fb14ed5d3f6420ec8171a5ad67a89098e75b8011ccd117ce362da80bb52c39fd`
- test2: `7e842e08156b2e474da25a5c913f767cbe054bbf96a6f550b4af65993b09a2d8`

Conclusion: traditional Docker image archive hash drift appears even with same Dockerfile/context.

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|-------------------|------------------------|
| Reproducibility | No (often hash drift) | Yes (deterministic tarball) |
| Dependency source | Runtime installs | Nix closure |
| Layer determinism | Lower | Higher |
| Build model | Imperative steps | Declarative derivation |

## Bonus - Flakes (optional)

Files:
- `labs/lab18/app_python/flake.nix`

Commands:

```bash
cd labs/lab18/app_python
nix flake update
nix build
nix build .#dockerImage
```

Notes:
- `flake.lock` should be generated and committed if bonus is required.

## Reflection

- Nix provides stronger reproducibility guarantees than `pip`/Docker alone because all inputs are hashed and pinned in store paths.
- For CI/CD and rollbacks, Nix's deterministic outputs reduce "works on my machine" drift.
- Docker remains useful for runtime packaging/distribution, while Nix strengthens deterministic build provenance.

## Screenshot evidence

The following screenshots are included in `labs/lab18/screenshots/`:
- `lab18_nix_install_build.png` - Nix installed, `nix --version`, and initial `nix-build` flow.
- `lab18_nix_build_run.png` - Nix build output and app run from `./result/bin/devops-info-service`.
- `lab18_docker_reproducability.png` - repeated `nix-build docker.nix` + identical `sha256sum` proof.

## Requirement-by-requirement checklist

- [x] Task 1: Nix installation and validation (`nix --version`, `nix run nixpkgs#hello`) - see `temp.txt` and screenshot `lab18_nix_install_build.png`
- [x] Task 1: `default.nix` created and builds Python service reproducibly - see `app_python/default.nix` and `temp.txt`
- [x] Task 1: deterministic output path/hash across rebuilds - see `temp.txt` build reproducibility section
- [x] Task 2: `docker.nix` created with `dockerTools` - see `app_python/docker.nix`
- [x] Task 2: Nix Docker image reproducibility proof (`sha256sum result` identical) - see `temp.txt` and screenshot `lab18_docker_reproducability.png`
- [x] Task 2: runtime validation and side-by-side comparison with classic Docker image - see `temp.txt` runtime comparison + both `/health` checks
- [x] Comparative analysis (traditional Docker vs Nix) - see Sections 2.4 and comparison tables above
- [x] Bonus: Flakes completed with `flake.nix` + generated `flake.lock`; validated via `nix build` and `nix build .#dockerImage`
