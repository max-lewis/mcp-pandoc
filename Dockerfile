FROM debian:bookworm-slim

# Cache-buster so Railway always rebuilds with the latest edits
ARG APP_REV=2025-11-08-fixed
RUN echo "APP_REV=$APP_REV"

# Non-interactive apt (prevents locale / tz prompts)
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

# ---- System packages ----
# Python + venv/pip
# Pandoc (converter)
# TeX Live minimal set (includes lmodern.sty + XeLaTeX)
# Fonts and Ghostscript for PDF rendering
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
    fonts-dejavu fonts-liberation fontconfig ghostscript ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Hard fail if lmodern.sty isn’t found
RUN kpsewhich lmodern.sty

# Show versions in build log
RUN xelatex --version && pandoc -v

# ---- Python deps in a virtualenv ----
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
ENV PATH="/venv/bin:${PATH}" APP_REV="${APP_REV}"

# ---- App code ----
COPY server.py /app/server.py

# ---- Web server ----
EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["/bin/sh","-c"]
CMD ["uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
