FROM pandoc/latex:latest

# Install Python + FastAPI runtime
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# App deps
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

WORKDIR /app
COPY server.py /app/server.py

# OPTIONAL: if you want ready-made defaults/templates from the fork,
# uncomment the next line (and ensure that path exists in your repo)
# COPY examples/defaults /templates

EXPOSE 8080
ENV PORT=8080
CMD ["sh","-c","uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
