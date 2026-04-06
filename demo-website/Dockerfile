FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime tools required by app:
# - dig (dnsutils)
# - unbound-control (unbound package)
# - redis-cli (redis-tools)
RUN apt-get update \
    && apt-get install -y --no-install-recommends dnsutils unbound redis-tools ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8080

CMD ["python", "-m", "backend.app"]
