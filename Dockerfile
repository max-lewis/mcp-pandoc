FROM debian:bookworm-slim

# Force rebuild so Railway doesn’t reuse cached layers
ARG CACHE_BUSTER=2025-11-08-04-20
RUN echo "cache-buster=$CACHE_BUSTER"

# System deps: Python + venv, Pandoc, LaTeX engine + fonts (incl. lmodern)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    texlive \
    texlive-xetex \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    fonts-lmodern \
    fonts-dejavu fonts-liberation fontconfig \
    ghostscript \
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
