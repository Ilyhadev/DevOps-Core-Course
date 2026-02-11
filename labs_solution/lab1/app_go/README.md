## Lab 1 Bonus, SD-02 Ilia Kliantsevich
### Overview

This is the bonus Lab 1 implementation in Go. It implements the same two endpoints as the Python app:
- GET /  — returns service, system, runtime, request information and endpoints
- GET /health — simple health check

### Build & Run

Requirements: Go 1.20+

Build:

```bash
go build -o devops-info-service ./
```

Run:

```bash
# default port 8080
./devops-info-service

# custom port
PORT=3000 ./devops-info-service
```

### API Endpoints

- GET /  - Service and system information
- GET /health - Health check

### Configuration

- HOST (default 0.0.0.0)
- PORT (default 5000)

### Notes

- The JSON structure mirrors the Python version from Task 1 for parity (the `python_version` field contains the Go runtime version in this implementation).
- Comparisson between python and go binaries is done in `app_go/docs/LAB01.md`

### Docker (multi-stage)

Build (from repo root):
```bash
docker build -t iliadocker21/devops-info-go:lab02 \
  -f labs_solution/lab1/app_go/Dockerfile labs_solution/lab1/app_go
```

Run:
```bash
docker run --rm -d --name lab2_go -p 8081:8080 iliadocker21/devops-info-go:lab02 && sleep 0.8 && docker logs lab2_go --tail 50
```
Check:
```curl -s http://127.0.0.1:8081/ | jq```

Measure image size:
```bash
docker images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep devops-info-go
```

See more (outputs & commands) at ```app_go/docs/screenshots/*.png``` and ```app_go/docs/LAB02.md```.


### To Test
```go test -v
=== RUN   TestMainHandler
--- PASS: TestMainHandler (0.00s)
=== RUN   TestHealthHandler
--- PASS: TestHealthHandler (0.00s)
PASS
ok      devops-info-service     0.005s
```