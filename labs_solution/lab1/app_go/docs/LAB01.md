# LAB01 (Go) Submission

This document records the Lab 1 bonus implementation in Go.

## What was implemented

- GET / — returns the full JSON payload with `service`, `system`, `runtime`, `request` and `endpoints`.
- GET /health — returns a small health JSON with timestamp and uptime_seconds.
- Uptime calculation using process start time.
- System info collection (hostname, platform, arch, CPU count).
- Request parsing with support for `X-Forwarded-For`.

## Testing

See screenshots at ```app_go/docs/screenshots``` to see explicit tests on default case.

Case with custom host and port:
```bash
HOST=127.0.0.1 PORT=1234 ./devops-info-service
2026/01/24 16:59:57 Starting devops-info-service on 127.0.0.1:1234
```
In another terminal:
```bash
> curl -s http://127.0.0.1:1234/health | jq
{
  "status": "healthy",
  "timestamp": "2026-01-24T14:00:04Z",
  "uptime_seconds": 6
}
> curl -s http://127.0.0.1:1234/ | jq          
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go"
  },
  "system": {
    "hostname": "AsusTuf",
    "platform": "Linux",
    "platform_version": "Linux Mint 22.2",
    "architecture": "amd64",
    "cpu_count": 16,
    "python_version": "n/a",
    "go_version": "go1.22.2"
  },
  "runtime": {
    "uptime_seconds": 24,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-01-24T14:00:22Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/8.5.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

## Notes

- The JSON keys are the same as the Python lab for compatibility and easy comparison. The `python_version` field contains the Go runtime version string for parity.

## Size comparison (measured)

Measured artifacts from this lab run (recorded while preparing the submission):

- Go binary (`app_go/devops-info-service`): 7,310,378 bytes (~7.31 MB)
- Python app (source tree, uncompressed): ~328K (du -sh result)
- Python tarball (`app_python.tar.gz`): 258,131 bytes (~252.3 KB)

Short comparison (lab context):

- The Go binary is a single static executable that includes the Go runtime, stdlib code used by your program (notably `net/http` and `encoding/json`), and symbol/debug information when built without stripping - which is why it appears much larger.
- The Python distribution is small because it is just source files (the Python interpreter/runtime is separate on the target system). Packaging the Python app into a tar.gz yields a small archive (~258 KB).

Takeaway: for this lab comparison, the Go build produces a larger single artifact (convenient single-file deployable) while the Python app is smaller as source — both are valid tradeoffs depending on your deployment needs.

## How to re-measure (copy-paste)

Run these commands from the repository root (or from `labs_solution/lab1/app_go` / `app_python` as indicated).

```bash
# Measure the existing Go binary (in app_go)
cd labs_solution/lab1/app_go
echo "Go binary (human):" && ls -lh ./devops-info-service
echo "Go binary (bytes):" && stat -c%s ./devops-info-service
echo "Go binary (disk usage):" && du -h ./devops-info-service

# Measure the Python app sizes (from repo root)
cd ../../app_python
echo "Python source tree (du):" && du -sh .
echo "Create tar.gz for measurement:" && tar -czf ../app_python.tar.gz .
echo "Python tarball (human):" && ls -lh ../app_python.tar.gz
echo "Python tarball (bytes):" && stat -c%s ../app_python.tar.gz

# Cleanup optional artifact
rm ../app_python.tar.gz ./devops-info-service.opt
```

Run the sequence to reproduce the numbers in this document and compare the raw Go binary vs the Python tarball.


