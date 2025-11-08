FROM pandoc/latex:latest

# Alpine uses apk; install Python + pip
RUN apk add --no-cache python3 py3-pip

# ---- Python deps in a virtualenv (PEP 668 safe) ----
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
 && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt
# Make venv tools (uvicorn, etc.) first on PATH
ENV PATH="/venv/bin:${PATH}"

# ---- App code ----
WORKDIR /app
COPY server.py /app/server.py

EXPOSE 8080
ENV PORT=8080
CMD ["sh","-c","uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
