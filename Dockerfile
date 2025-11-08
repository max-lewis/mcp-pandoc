FROM debian:bookworm-slim

ARG APP_REV=2025-11-08-wkhtml-final
RUN echo "APP_REV=$APP_REV"

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

# Python + Pandoc + wkhtmltopdf + fonts (small; no TeX at all)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    wkhtmltopdf \
    fonts-dejavu fonts-liberation fontconfig ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Sanity: show versions (appears in build logs)
RUN wkhtmltopdf --version && pandoc -v

WORKDIR /app

# Python deps in a virtualenv
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
ENV PATH="/venv/bin:${PATH}" APP_REV="${APP_REV}"

# App
COPY server.py /app/server.py

EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["/bin/sh","-c"]
CMD ["uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
