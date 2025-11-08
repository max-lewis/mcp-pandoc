FROM pandoc/latex:latest

# Alpine packages: Python, pip, TeX engine + fonts (for PDF)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    texlive \
    texlive-xetex \
    ttf-dejavu \
    fontconfig \
    ghostscript

# ---- Python deps in a virtualenv (PEP 668 safe) ----
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
ENV PATH="/venv/bin:${PATH}"

# ---- App code ----
WORKDIR /app
COPY server.py /app/server.py

# ---- Run the API ----
EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["/bin/sh","-c"]
CMD ["uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
