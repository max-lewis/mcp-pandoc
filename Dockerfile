FROM debian:bookworm-slim

# Keep Railway from reusing old layers when you update
ARG APP_REV=2025-11-08-smalltex
RUN echo "APP_REV=$APP_REV"

# Noninteractive apt + minimal locale
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

# Python, Pandoc, and a curated TeX Live set that includes lmodern + XeLaTeX
# IMPORTANT: Do NOT install texlive-full (too large for Railway’s 4 GB limit).
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    texlive-base \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-lm \
    texlive-xetex \
    fonts-dejavu fonts-liberation fontconfig ghostscript ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# HARD GUARANTEE: fail the build now if lmodern.sty isn't present
RUN kpsewhich lmodern.sty

# (Optional) show versions in build log
RUN xelatex --version && pandoc -v

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
