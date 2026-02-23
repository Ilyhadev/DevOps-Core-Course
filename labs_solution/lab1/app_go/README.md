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
