"""
DevOps Info Service - minimal Flask implementation for Lab 1
"""

import logging
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

# Application metadata
SERVICE_NAME = "devops-info-service"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = "DevOps course info service"
FRAMEWORK = "Flask"

# Configuration from environment
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# App and logging
app = Flask(__name__)
# Use DEBUG env to control logger level so that `DEBUG=True` prints debug logs
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
if DEBUG:
    logger.debug("Debug logging enabled")
logger.info("Application starting...")

START_TIME = datetime.now(timezone.utc)


@app.before_request
def log_request_info():
    """Log basic request information at debug level
        for tracing during development.

    This uses debug level
        so it can be enabled without flooding production logs.
    """
    try:
        remote = request.remote_addr
        if not remote:
            remote = request.headers.get("X-Forwarded-For")
        user_agent = request.headers.get("User-Agent")
        logger.debug(
            "Request: %s %s from %s - UA: %s",
            request.method,
            request.path,
            remote,
            user_agent,
        )
    except Exception:
        # Don't let logging errors break request handling
        logger.exception("Failed to log request info")


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
    logger.info("Handling main endpoint request")
    system = get_system_info()
    uptime = get_uptime()
    now = datetime.now(timezone.utc).isoformat()

    client_ip = request.remote_addr or (
        request.headers.get("X-Forwarded-For") or ""
    )

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
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime,
        }
    )


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found",
                    "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    resp = jsonify(
        {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    )
    return resp, 500


if __name__ == "__main__":
    logger.info(
        "Starting %s on %s:%s (debug=%s)", SERVICE_NAME, HOST, PORT, DEBUG
    )
    app.run(host=HOST, port=PORT, debug=DEBUG)
