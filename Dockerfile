FROM debian:bookworm-slim

# Force a fresh rebuild so Railway doesn’t reuse an old layer
ARG APP_REV=2025-11-08-12-25
RUN echo "APP_REV=$APP_REV"

# System deps:
# - Python + venv/pip
# - Pandoc
# - TeX Live base + LaTeX base/recommended/extra (includes lmodern.sty)
# - Fonts (Latin Modern + common), XeLaTeX engine, Ghostscript
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    texlive-base \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-xetex \
    fonts-lmodern \
    fonts-dejavu fonts-liberation fontconfig \
    ghostscript ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Sanity checks (fail the build if lmodern is still missing)
RUN kpsewhich lmodern.sty && xelatex --version && pandoc -v

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
