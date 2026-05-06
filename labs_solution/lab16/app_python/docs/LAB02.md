# LAB02 — Containerization (Python)

## Summary
- Dockerfile: `python:3.13-slim`, non-root user, dependencies installed before code, uses `gunicorn` as WSGI server.
- `.dockerignore` added to minimize build context.
- Reproducible build/run commands and measurements included below.

## Docker
- Docker Hub repo URL & see screenshot of push in app_python/docs/screenshots/python_docker_push.png & see tag name (updated in screenshot last_docker_tag_used.png):
```
https://hub.docker.com/r/iliadocker21/devops-info-python
```

## Docker Best Practices Applied
- **Non-Root User**:
  - Why: Reduces attack surface and the impact of a container escape; aligns with lab requirement. Running as root could allow privilege escalation if the container is compromised.
  - Dockerfile snippet:
    ```dockerfile
    RUN groupadd --gid 1000 app \
     && useradd --uid 1000 --gid app --shell /usr/sbin/nologin --create-home app
    USER app
    ```

- **Dependency Layer Separation (Cache Deps Before Copying App Code)**:
  - Why: Changing application code won't invalidate the dependency layer, significantly speeding iterative builds by leveraging Docker's cache mechanism.
  - Dockerfile snippet:
    ```dockerfile
    COPY requirements.txt ./
    RUN pip install --no-cache-dir -r requirements.txt \
        && pip install --no-cache-dir gunicorn
    ```

- **Minimal Build Context via `.dockerignore`**:
  - Why: Smaller context leads to faster builds and less chance of accidentally copying secrets/large files, improving security and efficiency.
  - Example entries: `venv/`, `__pycache__/`, `docs/screenshots/`.

- **Use a Production WSGI Server (`gunicorn`) Instead of Flask Dev Server**:
  - Why: Dev server is single-threaded and not meant for production; `gunicorn` provides workers and better fault isolation, handling concurrent requests more reliably.
  - Dockerfile snippet (CMD):
    ```dockerfile
    CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--workers", "1", "--threads", "2"]
    ```

## Image Information & Decisions
- **Base Image Chosen**: `python:3.13-slim`
  - Why: Official, maintained, smaller than full `python` images (removes non-essential packages while keeping compatibility), and widely used in production for Python apps.
- **Final Image Size**: 123,650,284 bytes (~124 MB)
  - Assessment: Acceptable for a Python + runtime image; larger than a compiled static binary due to the interpreter, libraries, and dependencies, but optimized for interpreted languages.
- **Layer Structure (High Level)**:
  1. Base `python:3.13-slim`
  2. OS/user setup
  3. Dependency installation (cached)
  4. Application files
  5. Ownership and runtime user
- **Optimization Choices Made**:
  - Installed dependencies before copying app source to leverage layer cache.
  - Added `.dockerignore` to reduce build context.
  - Switched to a production WSGI server (`gunicorn`).
  - Used `--no-cache-dir` in pip to avoid caching pip downloads in the image, keeping it slimmer.

## Build & Run (Captured Output)
These are the exact commands and outputs captured when building/running locally on 2026-01-31. See screenshot in app_python/docs/screenshots/docker_py_build_run.png.

- Build:
```
docker build app_python/ -t lab2_py
```
- Build summary (trimmed):
```
[+] Building 1.9s (13/13) FINISHED                                                                                                                                         docker:default
 => [internal] load build definition from Dockerfile                                                                                                                                 0.0s
 => => transferring dockerfile: 826B                                                                                                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                                                  1.5s
 => [auth] library/python:pull token for registry-1.docker.io                                                                                                                        0.0s
 => [internal] load .dockerignore                                                                                                                                                    0.0s
 => => transferring context: 238B                                                                                                                                                    0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:51e1a0a317fdb6e170dc791bbeae63fac5272c82f43958ef74a34e170c6f8b18                                                            0.0s
 => [internal] load build context                                                                                                                                                    0.0s
 => => transferring context: 1.91kB                                                                                                                                                  0.0s
 => CACHED [2/7] RUN groupadd --gid 1000 app  && useradd --uid 1000 --gid app --shell /usr/sbin/nologin --create-home app                                                            0.0s
 => CACHED [3/7] WORKDIR /app                                                                                                                                                        0.0s
 => CACHED [4/7] COPY requirements.txt ./                                                                                                                                            0.0s
 => CACHED [5/7] RUN pip install --no-cache-dir -r requirements.txt     && pip install --no-cache-dir gunicorn                                                                       0.0s
 => [6/7] COPY app.py README.md ./                                                                                                                                                   0.0s
 => [7/7] RUN chown -R app:app /app                                                                                                                                                  0.3s
 => exporting to image                                                                                                                                                               0.0s
 => => exporting layers                                                                                                                                                              0.0s
 => => writing image sha256:60e5de0487c9dc82af19c4e169...
```

- Run (startup logs; captured on 2026-01-31):
```
docker run --rm -d --name lab2_py -p 8080:8080 iliadocker21/devops-info-python:lab02 && sleep 0.8 && docker logs lab2_py --tail 20
563b970246655aac6a9ba4480ccd35b6e55ae9dd125788c7f74a6c9bbd206b5a
[2026-01-31 11:48:36 +0000] [1] [INFO] Starting gunicorn 24.1.1
[2026-01-31 11:48:36 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2026-01-31 11:48:36 +0000] [1] [INFO] Using worker: gthread
[2026-01-31 11:48:36 +0000] [7] [INFO] Booting worker with pid: 7
2026-01-31 11:48:36,725 - app - INFO - Application starting...
```

- Test (Endpoint Outputs; see screenshot in app_python/docs/screenshots/docker_example_work.png):
```
# /health
{
  "status": "healthy",
  "timestamp": "2026-01-31T11:49:06.247175+00:00",
  "uptime_seconds": 29
}

# / (pretty-printed JSON, trimmed)
{
  "service": {"name": "devops-info-service", "version": "1.0.0", ...},
  "system": {"hostname": "2d63f130b514", "platform": "Linux", ...},
  "runtime": {"uptime_seconds": 35, ...}
}
```

Final image size (human-readable):
```
docker images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep devops-info-python
iliadocker21/devops-info-python:lab02   124MB
```

Exact bytes and details for the final image (captured on 2026-01-31):
```
docker image inspect iliadocker21/devops-info-python:lab02 --format='{{.Id}} {{.RepoTags}} {{.Size}}'    
sha256:60e5de0487c9dc82af19c4e169... [iliadocker21/devops-info-python:lab02 iliadocker21/devops-info-python:v1.0.0-4dfe74c lab2_py:latest] 123650284
```

## Technical Analysis
- **Why the Dockerfile Works**:
  - Dependencies installed first produce a stable cached layer; the final image only contains runtime artifacts and the app source owned by a non-root user. This ensures efficient builds and a secure, minimal runtime.

- **What Happens if You Change Layer Order (e.g., Copy App Before Deps)**:
  - Copying app first will invalidate the layer cache for dependency installation on every source change, making rebuilds much slower and less efficient.

- **How `.dockerignore` Improves the Build**:
  - Reduces build context sent to the daemon (faster) and prevents accidentally packaging large or sensitive files, enhancing build speed and security.

## Security Benefits Discussed
The implementation enhances security by:
- **Non-Root User**: Prevents privilege escalation; processes run with limited permissions, reducing damage from breaches.
- **Minimal Files Copied**: Only necessary files (e.g., app.py, requirements.txt) are included, lowering the risk of including secrets or vulnerable code.
- **No Secrets in Image**: Environment variables (e.g., PORT) are runtime-only, avoiding baked-in credentials.
- **Production Server**: `gunicorn` is more secure than Flask's dev server, which warns about production use due to vulnerabilities.
- **Slim Base Image**: Fewer packages mean fewer CVEs; aligns with least-privilege principle, making scans (e.g., Trivy) cleaner.

Overall, this reduces attack surface compared to root-run, bloated images.

## Challenges & Solutions
- **Challenge**: Image size (Python interpreter + deps) is naturally larger than a compiled static binary.
  - Solution/Lesson: For deployment size-sensitive workloads, prefer distroless/scratch with compiled artifacts, or use slim images and remove unneeded deps. Here, `python:3.13-slim` balances size and compatibility.

- **Challenge**: Ensuring the container binds to the expected PORT and listens on 0.0.0.0.
  - Solution: Read `PORT` from env and use `gunicorn -b 0.0.0.0:$PORT` in the Dockerfile/CMD.

# Tagging Strategy (Concrete for This Repo)
- Example tag flow used in this submission:
  - `iliadocker21/devops-info-python:lab02` — local/dev snapshot used during development.
  - `iliadocker21/devops-info-python:v1.0.0-4dfe74c` — reproducible release tag that embeds a short git SHA.

- Why tag this way:
  - `lab02` is to show that context is learning experience during lab.
  - `v1.0.0-<GITSHA>` gives a human-friendly version plus an immutable digest linked to a commit.

- Commands used in this workspace:
```bash
# get short git sha from repo root
GITSHA=$(git rev-parse --short=7 HEAD)

# tag the locally-built image with a reproducible release tag
docker tag iliadocker21/devops-info-python:lab02 \
  iliadocker21/devops-info-python:v1.0.0-$GITSHA

# push the new tag to Docker Hub
docker login
docker push iliadocker21/devops-info-python:v1.0.0-$GITSHA
```

- Example push output (can be seen in app_python/docs/screenshots/python_docker_push.png):
```
The push refers to repository [docker.io/iliadocker21/devops-info-python]
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
docker pull iliadocker21/devops-info-python:v1.0.0-$GITSHA
docker image inspect iliadocker21/devops-info-python:v1.0.0-$GITSHA \
  --format 'ID: {{.Id}} Tags: {{.RepoTags}} Size: {{.Size}}'
```

## Short Q&A (Lab Topics)
- **Layer Caching — Why Does the Order of COPY Commands Matter?**
  - Docker builds images as a sequence of layers. Each Dockerfile instruction creates a new layer. When you change a file that was copied in an earlier layer, Docker invalidates that layer and all following layers. By copying `requirements.txt` and installing dependencies before copying application code, changes to application files won't force re-installation of dependencies. This speeds rebuilds and reduces network usage.

- **Non-Root User — How Do You Create and Switch to a Non-Root User?**
  - In the Dockerfile you create a group/user with `groupadd`/`useradd` (or `addgroup`/`adduser` on Alpine) and use the `USER` directive to switch the subsequent image steps and container runtime to that user. Example:
    ```dockerfile
    RUN groupadd --gid 1000 app \
     && useradd --uid 1000 --gid app --shell /usr/sbin/nologin --create-home app
    USER app
    ```
  - This ensures processes inside the container do not run as root, which reduces the impact of potential vulnerabilities.

- **Base Image Selection — What's the Difference Between Slim, Alpine, and Full Images?**
  - `full` (e.g., `python:3.13`) contains a full Debian/Ubuntu userland and most tooling — larger but very compatible.
  - `slim` (e.g., `python:3.13-slim`) is smaller: it removes many non-essential packages but keeps glibc and Debian userland, offering good compatibility with significantly less size.
  - `alpine` is very small and uses musl libc rather than glibc, which yields much smaller images but can cause compatibility issues with binary wheels or C extensions. Choose slim for Python apps where compatibility matters and base size should be reduced.

- **Dependency Installation — Why Copy `requirements.txt` Separately from Application Code?**
  - Copying `requirements.txt` and running `pip install` before copying the rest of the app creates an image layer that only changes when requirements change. This enables Docker to reuse the cached layer during code changes, significantly speeding iterative builds and reducing data transfer.