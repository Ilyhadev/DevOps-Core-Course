## Lab 1, SD-02 Ilia Kliantsevich

### Overview

This is a minimal Python implementation, which exposes two HTTP endpoints:
- `GET /` - returns service, system and runtime information
- `GET /health` - simple healthcheck JSON

### Prerequisites
Python version: Python 3.11+ (tested with Python 3.12.3)
Dependencies: Flask==3.1.0

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the application

```bash
python app.py
# or with custom port
PORT=8080 python app.py
```

### API Endpoints

- GET /  - Service and system information
- GET /health - Health check

### Configuration

- HOST (default 0.0.0.0)
- PORT (default 5000)
- DEBUG (default False)

### Docker

This section explains the command patterns to build, run and pull your containerized application. I use my dockerhub username to show how i exactly did it.

- Build (pattern):
  ```bash
  docker build -t iliadocker21/<repo>:<tag> -f <path-to-Dockerfile> <build-context>
  # example: docker build -t iliadocker21/devops-info-python:lab02 -f labs_solution/lab1/app_python/Dockerfile labs_solution/lab1/app_python
  ```

- Run (pattern):
  ```bash
  docker run --rm -p <host-port>:<container-port> -e PORT=<container-port> iliadocker21/<repo>:<tag>
  # example: docker run --rm -p 8080:8080 -e PORT=8080 iliadocker21/devops-info-python:lab02
  ```

- Pull (pattern):
  ```bash
  docker pull iliadocker21/<repo>:<tag>
  # example: docker pull iliadocker21/devops-info-python:lab02
  ```

- Tagging (pattern):
  ```bash
  docker tag <local-image>:<local-tag> iliadocker21/<repo>:<tag>
  # local image is the name:tag you built locally, for example devops-info-python:lab02
  ```

- Push to registry (pattern):
  ```bash
  docker login
  docker push iliadocker21/<repo>:<tag>
  ```


