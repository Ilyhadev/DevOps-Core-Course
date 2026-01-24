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

