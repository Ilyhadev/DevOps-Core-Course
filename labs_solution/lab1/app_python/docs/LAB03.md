# Lab 3 — Continuous Integration (CI/CD) — Python

## Summary
- Testing: pytest with 3 unit tests covering all endpoints
- CI/CD: GitHub Actions workflow with test, lint, Docker build/push
- Versioning: CalVer (YYYY.MM.DD) for Docker tags
- Best practices: Caching, path filters, job dependencies, Snyk security

## Testing

### Framework Choice
I choose **pytest** because:
- Simple, readable syntax (no boilerplate)
- Fixtures for setup/teardown
- Easy to run locally: `pytest -v`
- Works well with Flask test client
- Integrates into CI pipelines naturally

### Tests Written
See `tests/test_app.py`:
- `test_index_structure()` - Validates `GET /` returns correct JSON structure (service, system, runtime, request, endpoints fields)
- `test_health_endpoint()` - Validates `GET /health` returns status + timestamp
- `test_404_returns_json()` - Validates error response is JSON on 404

### Test Output (Real Run)
```bash
(venv) $ pytest -v
================================================================ test session starts ================================================================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
collected 3 items

tests/test_app.py::test_index_structure PASSED                                                                                                [ 33%]
tests/test_app.py::test_health_endpoint PASSED                                                                                                [ 66%]
tests/test_app.py::test_404_returns_json PASSED                                                                                               [100%]

================================================================= 3 passed in 0.15s ================================================================
```

### How to Run Locally
```bash
# Install test dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest -v
```

## GitHub Actions Workflow

### Trigger Strategy
**When:** Pushes or PRs to `main`, `master`, `lab03` branches  
**Path filter:** Only when `labs_solution/lab1/app_python/**` or workflow file changes  
**Why path filter?** Monorepo optimization — avoid redundant builds when only Go code changes

### Workflow File
- Location: `.github/workflows/python-ci.yml`
- Stages:
  1. **test-and-lint** → pytest, flake8
  2. **docker-build-push** → Build Docker image, push to Docker Hub (depends on stage 1)

### Versioning Strategy
**CalVer format:** `YYYY.MM.DD` (e.g., `2026.02.07`)  
**Docker tags created:**
- `iliadocker21/devops-info-python:2026.02.07` (immutable date tag)
- `iliadocker21/devops-info-python:latest` (rolling latest)

**Why CalVer?** Services deploy frequently; time-based versioning is clearer than manual SemVer bumping. Automated in CI, no manual git tagging needed. Besides, in context of lab assigment time-based based versioning is much more informative. 


## Best Practices Implemented

### 1. Caching (50% Speed Improvement)
```yaml
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
```
**Impact:** First run ~120s, subsequent runs ~60s. Cache invalidates when requirements.txt changes.

### 2. Dependency Installation with Linting
```yaml
- name: Install dependencies
  run: |
    pip install -q -r requirements.txt
    pip install -q -r requirements-dev.txt
    
- name: Lint with flake8
  run: flake8 labs_solution/lab1/app_python --count --select=E9,F63,F7,F82 --show-source --statistics
```

### 3. Job Dependencies (Fail-Fast)
Docker build only runs if tests pass:
```yaml
docker-build-push:
  needs: test-and-lint
```

### 4. Security Scanning (Snyk)
```yaml
security-scan:
  name: Security Scan (Snyk)
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r labs_solution/lab1/app_python/requirements.txt
    - name: Run Snyk security scan
      uses: snyk/actions/python@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      continue-on-error: true
```
**Separate job** that scans `requirements.txt` for CVEs in dependencies. Uses `snyk/actions/python` (language-specific action). Runs in parallel with tests. Set to `continue-on-error: true` so build doesn't break on vulnerability findings (allows documenting findings before fixing).

**Setup required:** Add `SNYK_TOKEN` secret via GitHub repo settings (free tier at snyk.io).

### 5. Status Badge
Added to README:
```markdown
![CI status](https://github.com/Ilyhadev/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)
```

## Coverage

### Current Metrics
```
test_index_structure()   Validates JSON structure, field presence, types
test_health_endpoint()   Validates status code + timestamp response
test_404_returns_json()  Validates error handling returns JSON


```

Coverage: ~90% of core functionality (endpoints + response format)
```
cd /home/ilia/Desktop/vsCode/DevOps/DevOps-
Core-Course/labs_solution/lab1/app_python && pytest -v --cov=. --cov-report=term --cov-report=xml && echo -e "\n Coverage report generated in CI fo
rmat"
================================================================ test session starts ================================================================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0 -- /home/ilia/Desktop/vsCode/DevOps/DevOps-Core-Course/venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/ilia/Desktop/vsCode/DevOps/DevOps-Core-Course/labs_solution/lab1/app_python
plugins: cov-7.0.0
collected 3 items                                                                                                                                   

tests/test_app.py::test_index_structure PASSED                                                                                                [ 33%]
tests/test_app.py::test_health_endpoint PASSED                                                                                                [ 66%]
tests/test_app.py::test_404_returns_json PASSED                                                                                               [100%]

================================================================== tests coverage ===================================================================
__________________________________________________ coverage: platform linux, python 3.12.3-final-0 __________________________________________________

Name                Stmts   Miss  Cover
---------------------------------------
app.py                 64      8    88%
tests/__init__.py       0      0   100%
tests/test_app.py      34      0   100%
---------------------------------------
TOTAL                  98      8    92%
Coverage XML written to file coverage.xml
================================================================= 3 passed in 0.99s =================================================================

Coverage report generated in CI format
```
### What's Tested
- + All 3 endpoints (`/`, `/health`, error responses)
- + JSON structure and field types
- + HTTP response codes

### What's Not Tested (and Why)
- `get_system_info()` — Tested indirectly via `/` endpoint
- `get_uptime()` — Tested indirectly via `/` response
- Request logging — Would need logger mocking
- 500 errors — Hard to trigger without mocking internals

## Workflow Evidence
Successfull run: https://github.com/Ilyhadev/DevOps-Core-Course/actions/runs/21780187847
