FROM debian:bookworm-slim

# Force a fresh rebuild so Railway doesn’t reuse old layers
ARG APP_REV=2025-11-08-checked-texlivefull
RUN echo "APP_REV=$APP_REV"

# Python + Pandoc + full TeX Live + fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    texlive-full \
    fonts-dejavu fonts-liberation fontconfig ghostscript ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Sanity checks (will print versions; if something is missing the build would fail earlier)
RUN xelatex --version && pdflatex --version && pandoc -v

# Python deps in a virtualenv
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
ENV PATH="/venv/bin:${PATH}" APP_REV="${APP_REV}"

# App
COPY server.py /app/server.py

# Web server
EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["/bin/sh","-c"]
CMD ["uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
