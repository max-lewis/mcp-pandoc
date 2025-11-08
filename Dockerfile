FROM debian:bookworm-slim

# Force rebuild so Railway doesn’t reuse old layers
ARG APP_REV=2025-11-08-12-10
RUN echo "APP_REV=$APP_REV"

# System deps: Python + venv/pip, Pandoc (converter), Tectonic (PDF engine),
# fonts + fontconfig (for PDF), CA certs
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    tectonic \
    fonts-dejavu fonts-liberation fontconfig ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Python deps in a virtualenv
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
ENV PATH="/venv/bin:${PATH}"

# App
COPY server.py /app/server.py

# Web server
EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["/bin/sh","-c"]
CMD ["uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
