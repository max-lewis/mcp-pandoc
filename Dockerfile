FROM pandoc/latex:latest

# Alpine uses apk (not apt-get)
RUN apk add --no-cache python3 py3-pip

# App deps
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

WORKDIR /app
COPY server.py /app/server.py

# If you previously tried to copy example templates, comment it out for now
# COPY examples/defaults /templates

EXPOSE 8080
ENV PORT=8080
CMD ["sh","-c","uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
