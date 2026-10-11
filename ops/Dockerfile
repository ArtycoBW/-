FROM postgres:17-alpine
RUN apk add --no-cache python3
WORKDIR /opt/ops
COPY ops/worker.py ./worker.py
USER postgres
ENTRYPOINT ["python3", "-u", "/opt/ops/worker.py"]
