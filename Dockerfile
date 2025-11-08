FROM debian:bookworm-slim

# Rebuild cache-buster
ARG APP_REV=2025-11-08-no-lmodern
RUN echo "APP_REV=$APP_REV"

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8

# Python + Pandoc + a minimal TeX stack for XeLaTeX + fonts
# (no texlive-full, stays well under Railway's 4 GB image limit)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip \
    pandoc \
    texlive-base \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-xetex \
    fonts-dejavu fonts-liberation fontconfig ghostscript ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Optional: show versions in the build log
RUN xelatex --version && pandoc -v

WORKDIR /app

# Python deps in a virtualenv
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
ENV PATH="/venv/bin:${PATH}" APP_REV="${APP_REV}"

# App code + custom LaTeX template that does NOT load lmodern
COPY server.py /app/server.py
COPY latex-template.tex /app/latex-template.tex

EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["/bin/sh","-c"]
CMD ["uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
