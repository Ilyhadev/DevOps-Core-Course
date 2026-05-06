## Lab 12 - DevOps Info Service with Persistence

![CI status](https://github.com/Ilyhadev/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

### Overview

Flask-based microservice extended with visit counter persistence:
- `GET /` - returns service, system and runtime information (**increments visit counter**)
- `GET /health` - simple healthcheck JSON
- `GET /visits` - returns current visit count
- Counter persisted to `/data/visits`

### Prerequisites
Python version: Python 3.11+ (tested with Python 3.12.3)
Dependencies: Flask==3.1.0, prometheus-client, python-json-logger

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Testing (pytest)

I chose pytest as the test framework because it has concise syntax, powerful fixtures, and a large ecosystem of plugins. Tests live in `tests/` and use Flask's test client.

To run tests locally:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest -q
```

Notes:
- Framework: pytest (see `requirements-dev.txt`)
- Tests cover the main endpoint `/`, `/health` and the 404 handler. They assert JSON structure and basic types.


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


### How to Test Locally
Note: see expected output and more info in docs/LAB03 
```bash
# Install test dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest -v
```