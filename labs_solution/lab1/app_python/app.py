"""
DevOps Info Service - minimal Flask implementation for Lab 1
"""

import logging
import os
import platform
import socket
import sys
import time
from datetime import datetime, timezone

from flask import Flask, Response, g, jsonify, request
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pythonjsonlogger import jsonlogger

# Application metadata
SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

# Configuration from environment
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# App and JSON logging
app = Flask(__name__)
# Use DEBUG env to control logger level so that `DEBUG=True` prints debug logs
log_level = logging.DEBUG if DEBUG else logging.INFO

# Configure JSON logging
logging.basicConfig(
    level=log_level,
    format="%(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

# Add JSON formatter to handler
json_handler = logging.StreamHandler(sys.stdout)
json_formatter = jsonlogger.JsonFormatter()
json_handler.setFormatter(json_formatter)

# Remove default handler and add JSON handler
logger.handlers.clear()
logger.addHandler(json_handler)

logger.info("Application starting", extra={
    "service": SERVICE_NAME,
    "version": SERVICE_VERSION,
    "debug": DEBUG
})

START_TIME = datetime.now(timezone.utc)

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
)

# Application-specific metrics
endpoint_calls = Counter(
    "devops_info_endpoint_calls",
    "Endpoint calls",
    ["endpoint"],
)
system_info_duration = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time",
)


def _endpoint_label():
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return request.path or "unknown"


@app.before_request
def log_request_info():
    """Log request information in JSON format.
    
    This uses debug level so it can be enabled without flooding production logs.
    """
    try:
        remote = request.remote_addr
        if not remote:
            remote = request.headers.get("X-Forwarded-For")
        user_agent = request.headers.get("User-Agent")
        logger.debug(
            "Request received",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": remote,
                "user_agent": user_agent,
                "event_type": "request_received"
            }
        )
    except Exception as e:
        # Don't let logging errors break request handling
        logger.exception("Failed to log request info", extra={
            "error": str(e),
            "event_type": "logging_error"
        })


@app.before_request
def start_metrics_timer():
    g.start_time = time.perf_counter()
    http_requests_in_progress.inc()


@app.after_request
def record_request_metrics(response):
    endpoint = _endpoint_label()
    method = request.method
    status_code = str(response.status_code)

    duration = time.perf_counter() - getattr(g, "start_time", time.perf_counter())
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()
    http_requests_in_progress.dec()
    return response


def get_system_info():
    """Collect basic system information."""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
    }


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    human = (
        f"{hours} hour{'s' if hours != 1 else ''}, "
        f"{minutes} minute{'s' if minutes != 1 else ''}"
    )
    return {"seconds": seconds, "human": human}


@app.route("/")
def index():
    with system_info_duration.time():
        system = get_system_info()
    uptime = get_uptime()
    now = datetime.now(timezone.utc).isoformat()

    client_ip = request.remote_addr or (
        request.headers.get("X-Forwarded-For") or ""
    )

    logger.info(
        "Main endpoint called",
        extra={
            "event_type": "endpoint_main",
            "client_ip": client_ip,
            "status": 200
        }
    )
    endpoint_calls.labels(endpoint="/").inc()

    payload = {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": SERVICE_DESCRIPTION,
            "framework": FRAMEWORK,
        },
        "system": system,
        "runtime": {
            "uptime_seconds": uptime["seconds"],
            "uptime_human": uptime["human"],
            "current_time": now,
            "timezone": "UTC",
        },
        "request": {
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent"),
            "method": request.method,
            "path": request.path,
        },
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Service information",
            },
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check",
            },
        ],
    }
    return jsonify(payload)


@app.route("/health")
def health():
    uptime = get_uptime()["seconds"]
    logger.info(
        "Health check endpoint called",
        extra={
            "event_type": "endpoint_health",
            "status": 200,
            "uptime_seconds": uptime
        }
    )
    endpoint_calls.labels(endpoint="/health").inc()
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime,
        }
    )


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype="text/plain; version=0.0.4; charset=utf-8")


@app.errorhandler(404)
def not_found(error):
    logger.warning(
        "Not Found error",
        extra={
            "event_type": "error_404",
            "path": request.path,
            "method": request.method,
            "status": 404
        }
    )
    return jsonify({"error": "Not Found",
                    "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(
        "Internal Server Error",
        extra={
            "event_type": "error_500",
            "path": request.path,
            "method": request.method,
            "status": 500,
            "error": str(error)
        }
    )
    resp = jsonify(
        {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    )
    return resp, 500


if __name__ == "__main__":
    logger.info(
        "Application startup",
        extra={
            "event_type": "startup",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "host": HOST,
            "port": PORT,
            "debug": DEBUG
        }
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
