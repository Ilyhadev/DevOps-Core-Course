# LAB01 Submission

Framework choice & justification

Chosen framework: Flask

Justification:
- Flask is lightweight and easy to learn, which i useful for me as beginner in python & devops field.
- It has minimal ceremony: a small amount of code provides a functioning web service quickly.
- Flask's synchronous model is sufficient for the lab's task; the service is I/O-light and doesn't require async concurrency.
- Large ecosystem and community resources make troubleshooting and extending the app straightforward (addition to first point).

Why not FastAPI or Django?
- FastAPI is excellent for async, high-performance APIs and automatic schema generation, but its extra features are unnecessary for the simple endpoints required in this lab and add learning overhead for beginners.
- Django is a batteries-included framework with ORM, admin, and many features; it's overkill for a small single-file service and would distract from the course focus.

Screenshots are located in `docs/screenshots/`

## Best Practices Applied

This project follows a number of practical best practices. Each entry shows a short example (extracted from `app.py`) and explains why it matters.

- Clear function boundaries and docstrings

```python
def get_system_info():
		"""Collect basic system information."""
		return { 'hostname': socket.gethostname(), 'platform': platform.system() }
```

Why: Small, focused functions are easier to test and reason about. Docstrings make intent clear for future readers and tools.

- Configuration via environment variables

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
```

Why: Keeps secrets and environment-specific settings out of source control and allows the service to be configured in containers or CI.

- Centralized logging and a before-request logger

```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
@app.before_request
def log_request_info():
		logger.debug("Request: %s %s", request.method, request.path)
```

Why: Structured logging helps troubleshoot behavior in development and production. A before-request hook captures request context consistently.

- Error handlers

```python
@app.errorhandler(404)
def not_found(error):
		return jsonify({'error': 'Not Found', 'message': 'Endpoint does not exist'}), 404
```

Why: Returning JSON errors keeps API responses consistent and easier for clients or health checks to parse.

- Dependency pinning

Add exact versions in `requirements.txt` (e.g. `Flask==3.1.0`) so deployments are reproducible.


## API Documentation

Endpoints

- GET /  — Service and system information
- GET /health — Health check

Request examples (using curl)

```bash
# Main endpoint
curl -s http://127.0.0.1:5000/ | jq

# Health endpoint
curl -s http://127.0.0.1:5000/health | jq
```

Sample response (truncated) for GET /:

```json
> curl http://127.0.0.1:5000/ | jq      
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   689  100   689    0     0   218k      0 --:--:-- --:--:-- --:--:--  224k
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.5.0"
  },
  "runtime": {
    "current_time": "2026-01-24T11:32:52.591025+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours, 1 minute",
    "uptime_seconds": 94
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 16,
    "hostname": "AsusTuf",
    "platform": "Linux",
    "platform_version": "#37~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Nov 20 10:25:38 UTC 2",
    "python_version": "3.12.3"
  }
}
```

Sample response for GET /health:

```json
> curl -s http://127.0.0.1:5000/health | jq
{
  "status": "healthy",
  "timestamp": "2026-01-24T11:33:50.552606+00:00",
  "uptime_seconds": 152
}
```

## Testing notes

- Start the app:

```bash
> PORT=8080 python app.py 
2026-01-24 15:57:31,129 - __main__ - INFO - Application starting...
2026-01-24 15:57:31,130 - __main__ - INFO - Starting devops-info-service on 0.0.0.0:8080 (debug=False)
 * Serving Flask app 'app'
 * Debug mode: off
2026-01-24 15:57:31,133 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://10.69.0.88:8080
2026-01-24 15:57:31,133 - werkzeug - INFO - Press CTRL+C to quit
```
- Send curl commands on endpoints in another terminal:
```bash
> curl -s http://127.0.0.1:8080/ | jq
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.5.0"
  },
  "runtime": {
    "current_time": "2026-01-24T12:58:27.715381+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours, 0 minutes",
    "uptime_seconds": 56
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 16,
    "hostname": "AsusTuf",
    "platform": "Linux",
    "platform_version": "#37~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Nov 20 10:25:38 UTC 2",
    "python_version": "3.12.3"
  }
}

> curl -s http://127.0.0.1:8080/health | jq
{
  "status": "healthy",
  "timestamp": "2026-01-24T12:58:55.233348+00:00",
  "uptime_seconds": 84
}
```

- Try the endpoints with curl. I additionaly use `jq` to pretty-print JSON. For example:

```bash
curl http://127.0.0.1:5000/ | jq
```

- Here debug logs are:
```bash
> DEBUG=True PORT=8080 python app.py 
2026-01-24 16:27:02,616 - __main__ - DEBUG - Debug logging enabled
2026-01-24 16:27:02,616 - __main__ - INFO - Application starting...
2026-01-24 16:27:02,617 - __main__ - INFO - Starting devops-info-service on 0.0.0.0:8080 (debug=True)
 * Serving Flask app 'app'
 * Debug mode: on
2026-01-24 16:27:02,635 - werkzeug - INFO - WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://10.69.0.88:8080
2026-01-24 16:27:02,635 - werkzeug - INFO - Press CTRL+C to quit
2026-01-24 16:27:02,636 - werkzeug - INFO -  * Restarting with stat
2026-01-24 16:27:02,845 - __main__ - DEBUG - Debug logging enabled
2026-01-24 16:27:02,845 - __main__ - INFO - Application starting...
2026-01-24 16:27:02,846 - __main__ - INFO - Starting devops-info-service on 0.0.0.0:8080 (debug=True)
2026-01-24 16:27:02,860 - werkzeug - WARNING -  * Debugger is active!
2026-01-24 16:27:02,863 - werkzeug - INFO -  * Debugger PIN: 133-213-133
2026-01-24 16:27:07,254 - __main__ - DEBUG - Request: GET / from 127.0.0.1 - UA: curl/8.5.0
2026-01-24 16:27:07,254 - __main__ - INFO - Handling main endpoint request
2026-01-24 16:27:07,256 - werkzeug - INFO - 127.0.0.1 - - [24/Jan/2026 16:27:07] "GET / HTTP/1.1" 200 -
```
Look for screenshots at app_python/docs/screenshots. NOTE: i use jq from the start so all output is pretty printed!

## Challenges & Solutions (for Flask beginners)

Here are minor issues i faced (fixed with one browser search basically):

- "Port already in use"
	- Solution: pick a different `PORT` environment variable (e.g. `PORT=8080 python app.py`) or find/kill the process using the port.

- "Timestamps are confusing / timezone issues"
	- Solution: use timezone-aware datetimes (this project uses `datetime.now(timezone.utc).isoformat()`).

- "Logging doesn't show request details"
	- Solution: enable DEBUG logging locally and use the `@app.before_request` handler to log method/path/UA.


## GitHub Community

I followed the lab's instructions and performed the recommended social actions on GitHub.

Why this matters:

- Starring repositories helps discovery and signals appreciation - it bookmarks projects for later, increases project visibility, and encourages maintainers.
- Following developers keeps you informed about their work, makes it easier to learn from their commits and projects, and helps build a professional network for collaboration and support.

Actions taken: followed the professor and TAs listed in the lab instructions and several classmates.

## Static checking and formatting

For PEP8 checking and consistent formatting use the following developer tools.
Here i used flake8:
```bash
pip install --upgrade pip
pip install flake8 black isort
flake8 app.py
```

---

Screenshots are in `docs/screenshots/`.
