FROM debian:bookworm-slim

ARG APP_REV=2025-11-08-finalfix
RUN echo "APP_REV=$APP_REV"

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

# Minimal TeXLive set with all packages Pandoc’s default template needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    texlive-base \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    fonts-dejavu fonts-liberation fontconfig ghostscript ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Verify LaTeX can see core packages (will print paths in build logs)
RUN kpsewhich fontspec.sty && kpsewhich geometry.sty && kpsewhich hyperref.sty && kpsewhich xelatex.ini

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
ENV PATH="/venv/bin:${PATH}" APP_REV="${APP_REV}"

COPY server.py /app/server.py

EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["/bin/sh","-c"]
CMD ["uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
