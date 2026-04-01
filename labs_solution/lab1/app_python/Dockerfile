# Python app Dockerfile for Lab 2
# Base image: explicit, stable, slim variant
FROM python:3.13-slim

# runtime environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# create non-root user
RUN groupadd --gid 1000 app \
 && useradd --uid 1000 --gid app --shell /usr/sbin/nologin --create-home app

WORKDIR /app

# install system dependencies (curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# install runtime deps first to leverage Docker layer cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# copy only application code
COPY app.py README.md ./

# make sure files are owned by non-root user
RUN chown -R app:app /app

USER app

EXPOSE 8080
# use gunicorn for flask app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--workers", "1", "--threads", "2"]
