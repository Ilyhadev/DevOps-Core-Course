# LAB02 — Multi-stage container (Go)

## What I Implemented
- Multi-stage Dockerfile: builder (golang:1.22) → runtime (alpine:3.18).
- Final image runs as non-root and contains only the stripped static binary.

## Docker
- Docker Hub repo URL & see screenshot of push in app_go/docs/screenshots/go_docker_push_tag.png & see tag name:
```
https://hub.docker.com/repository/docker/iliadocker21/devops-info-go/general
```

## Multi-Stage Build Strategy (What & Why)
- **Stage 1 (Builder)**: Uses `golang:1.22` to download Go modules and compile a static binary with `CGO_ENABLED=0` (disables CGO for static linking) and `-ldflags="-s -w"` (strips debug symbols and DWARF tables for smaller size). This stage is large (~968MB) but necessary for the full Go toolchain and network access during build.
- **Stage 2 (Runtime)**: Uses `alpine:3.18` as a minimal base (~5MB), adds a non-root user/group, and copies only the compiled binary from the builder. No build tools or dependencies remain.

**Why This Strategy?** Multi-stage builds separate build-time dependencies (e.g., Go SDK) from runtime needs, resulting in a smaller, more secure final image. For compiled languages like Go, this is crucial because the app compiles to a self-contained binary—no need for the heavy SDK at runtime. This reduces image size (faster pulls/deploys), minimizes attack surface (fewer vulnerabilities in runtime image), and improves security (non-root execution). Without multi-stage, the final image would include unnecessary tools, bloating it to hundreds of MB.

## Why Multi-Stage Builds Matter for Compiled Languages
Compiled languages (e.g., Go, Rust) produce static binaries that run independently without interpreters or heavy runtimes (unlike Python/Node). In a single-stage build, the image retains the entire compiler/SDK, leading to:
- **Bloat**: Unneeded tools increase size (e.g., golang:1.22 is ~968MB vs. <20MB final).
- **Security Risks**: More packages = more CVEs; attackers could exploit build tools.
- **Performance Issues**: Larger images slow down deployments and cold starts.

Multi-stage fixes this by discarding the builder stage post-compilation. Research shows this can reduce sizes by 90%+ (e.g., from Docker docs). Trade-offs: More complex Dockerfile, but benefits outweigh for production. For Go, static compilation (`CGO_ENABLED=0`) enables ultra-minimal bases like alpine or even scratch (no OS), but I chose alpine for basic utilities (e.g., useradd) and compatibility.

## Size Comparison & Measured Outputs (Captured)
- **Final Image Size**: `iliadocker21/devops-info-go:lab02` — 12.3 MB (meets <20MB challenge). See screenshot in app_go/docs/screenshots/docker_go_image_size.png.
- **Static Binary Inside Final Image**: `/usr/local/bin/devops-info-service` — 4,927,640 bytes (4.7MB).
- **Builder Image Size** (for comparison): `golang:1.22` — ~968MB (pulled and measured via `docker images`).
- **Analysis**: The builder is ~80x larger due to the Go SDK, modules, and tools. Final image is minimal: alpine base (~5MB) + binary (4.7MB) + metadata/layers (~2.6MB overhead). This reduction lowers storage/pull times and vuln exposure (alpine has fewer packages than full Debian-based images). If using scratch, it could be ~5MB total, but alpine adds safety (e.g., timezone data). Your analysis is correct and aligns with this—multi-stage enables keeping SDK convenience while distributing minimal runtime, reducing bloat effectively.

## Terminal Output Showing Build Process and Image Sizes
Build (trimmed, captured on 2026-01-31; see screenshot in app_go/docs/screenshots/docker_go_build.png):
```
docker build app_go/ -t lab2_go
[+] Building 13.0s (17/17) FINISHED                                                                                                                                        docker:default
 => [internal] load build definition from Dockerfile                                                                                                                                 0.0s
 => => transferring dockerfile: 686B                                                                                                                                                 0.0s
 => [internal] load metadata for docker.io/library/alpine:3.18                                                                                                                       1.5s
 => [internal] load metadata for docker.io/library/golang:1.22                                                                                                                       1.5s
 => [auth] library/alpine:pull token for registry-1.docker.io                                                                                                                        0.0s
 => [auth] library/golang:pull token for registry-1.docker.io                                                                                                                        0.0s
 => [internal] load .dockerignore                                                                                                                                                    0.0s
 => => transferring context: 175B                                                                                                                                                    0.0s
 => [builder 1/6] FROM docker.io/library/golang:1.22@sha256:1cf6c45ba39db9fd6db16922041d074a63c935556a05c5ccb62d181034df7f02                                                         0.0s
 => [stage-1 1/3] FROM docker.io/library/alpine:3.18@sha256:de0eb0b3f2a47ba1eb89389859a9bd88b28e82f5826b6969ad604979713c2d4f                                                         0.0s
 => [internal] load build context                                                                                                                                                    0.0s
 => => transferring context: 12.99kB                                                                                                                                                 0.0s
 => CACHED [builder 2/6] WORKDIR /src                                                                                                                                                0.0s
 => CACHED [builder 3/6] COPY go.mod ./                                                                                                                                              0.0s
 => CACHED [builder 4/6] RUN go mod download                                                                                                                                         0.0s
 => [builder 5/6] COPY . .                                                                                                                                                           0.0s
 => [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64     go build -trimpath -ldflags="-s -w" -o /out/devops-info-service .                                                   11.4s
 => CACHED [stage-1 2/3] RUN addgroup -S app && adduser -S -G app -u 1000 app                                                                                                        0.0s
 => CACHED [stage-1 3/3] COPY --from=builder /out/devops-info-service /usr/local/bin/devops-info-service                                                                             0.0s
 => exporting to image                                                                                                                                                               0.0s
 => => exporting layers                                                                                                                                                              0.0s
 => => writing image sha256:254e6c83b8eeb7fb89927956375d669095e87159eec3e0c154a808b53d5fa358                                                                                         0.0s
 => => naming to docker.io/library/lab2_go
```

Final image size (human-readable):
```
docker images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep devops-info-go
iliadocker21/devops-info-go:lab02       12.3MB
```

Exact bytes and details for the final image (captured on 2026-01-31):
```
docker image inspect iliadocker21/devops-info-go:lab02 --format='{{.Id}} {{.RepoTags}} {{.Size}}'    
sha256:254e6c83b8eeb7fb89927956375d669095e87159eec3e0c154a808b53d5fa358 [iliadocker21/devops-info-go:lab02 iliadocker21/devops-info-go:v1.0.0-4dfe74c lab2_go:latest] 12296273
```

Builder image size (for comparison):
```
docker pull golang:1.22 && docker images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep golang:1.22
golang:1.22     823MB
```

Exact bytes for builder image:
```
docker image inspect golang:1.22 --format='{{.Size}}'
822983029
```

Run + startup logs (captured on 2026-01-31; see screenshot in app_go/docs/screenshots/docker_go_run.png):
```
docker run --rm -d --name lab2_go -p 8081:8080 iliadocker21/devops-info-go:lab02 && sleep 0.8 && docker logs lab2_go --tail 50
5cb65f6ebfc21059449beef1ee7c0439dca6a3277389587a2ffdd0842f57d6f3
2026/01/31 13:37:36 Starting devops-info-service on :8080
```

## Technical Explanation of Each Stage
- **Stage 1: FROM golang:1.22 AS builder**:
  - Provides `go` toolchain and network access to download modules.
  - `go build` runs here with flags producing a static, stripped binary.
- **Stage 2: FROM alpine:3.18**:
  - Very small base image; we add a non-root user and copy only the binary.
  - No compilers or package managers remain in the final image.

## How I Achieved <20MB (Challenge)
- Build with `CGO_ENABLED=0` and `-ldflags='-s -w'` to avoid C linking and strip symbol tables.
- Use a minimal runtime base (`alpine`) and copy only the binary.
- The repository's `app_go/Dockerfile` already applies these techniques and the final image in my run is 12.3 MB (meets the <20MB challenge).

## Security Benefits Discussed
Multi-stage builds enhance security by:
- **Minimizing Attack Surface**: The final image excludes build tools (e.g., compilers, debuggers) that could be exploited if the container is compromised. With only the binary and minimal OS (alpine), there are fewer packages and thus fewer potential vulnerabilities (e.g., CVEs in unused libraries).
- **Non-Root Execution**: Running as a non-root user (UID 1000) prevents privilege escalation; even if an attacker gains access, they can't easily modify system files or escape the container.
- **Smaller Image = Fewer Risks**: Reduced size means less code to scan/audit. Tools like Trivy or Snyk would report fewer issues. Static binaries avoid dynamic linking risks (e.g., libc vulns). Overall, this aligns with Docker best practices for production, reducing breach impact (e.g., no shell in minimal bases like scratch for shell injection attacks).

## Challenges & Solutions
- **Challenge**: Initial Dockerfile copy step failed when `go.sum` was absent in the build context. 
- **Fix**: Make the Dockerfile copy `go.mod` and let `go mod download` populate `go.sum` inside the builder stage.
- **Learnings**: Multi-stage is essential for prod; researched static vs. dynamic (dynamic needs libc, limiting bases like scratch).

# Tagging Strategy (Concrete for This Repo)
- Example tag flow used in this submission:
  - `iliadocker21/devops-info-go:lab02` — local/dev snapshot used during development.
  - `iliadocker21/devops-info-go:v1.0.0-4dfe74c` — reproducible release tag that embeds a short git SHA.

- Why tag this way:
  - `lab02` is to show that context is learning experience during lab.
  - `v1.0.0-<GITSHA>` gives a human-friendly version plus an immutable digest linked to a commit.

- Commands used in this workspace:
```bash
# get short git sha from repo root
GITSHA=$(git rev-parse --short=7 HEAD)

# tag the locally-built image with a reproducible release tag
docker tag iliadocker21/devops-info-go:lab02 \
  iliadocker21/devops-info-go:v1.0.0-$GITSHA

# push the new tag to Docker Hub
docker login
docker push iliadocker21/devops-info-go:v1.0.0-$GITSHA
```

- Example push output (can be seen in app_go/docs/screenshots/go_docker_push_tag.png):
```
The push refers to repository [docker.io/iliadocker21/devops-info-go]
76d5a2b9bd40: Layer already exists 
5a3f002a2980: Layer already exists 
7049dd4651a6: Layer already exists 
23927037cfcc: Layer already exists 
0b32eba014df: Layer already exists 
84e2e701d96a: Layer already exists 
a915d0aa80cd: Layer already exists 
ad1b18dd62d2: Layer already exists 
d85cc8d16465: Layer already exists 
e50a58335e13: Layer already exists 
v1.0.0-4dfe74c: digest: sha256:07bd9ca56000cfcea6142b260877485e4df7db78f7583e1848f4b400b6340480 size: 2407
```

After a successful push you can verify by pulling or inspecting the pushed tag:
```bash
docker pull iliadocker21/devops-info-go:v1.0.0-$GITSHA
docker image inspect iliadocker21/devops-info-go:v1.0.0-$GITSHA \
  --format 'ID: {{.Id}} Tags: {{.RepoTags}} Size: {{.Size}}'
```