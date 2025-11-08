FROM pandoc/latex:latest
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
COPY http-wrapper/requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt
WORKDIR /app
COPY http-wrapper/server.py /app/server.py

# OPTIONAL: reuse the repo's defaults/templates so you get its examples immediately
# They live under examples/defaults in the repo
COPY examples/defaults /templates

EXPOSE 8080
ENV PORT=8080
CMD ["sh","-c","uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
