FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY atende VERSION ./
COPY src/ ./src/
COPY web/ ./web/
COPY exemplos/ ./exemplos/
RUN chmod +x atende
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python3 -c "import json, urllib.request; r = urllib.request.urlopen('http://127.0.0.1:8080/api/saude', timeout=3); assert json.load(r)['ok'] is True"
CMD ["./atende", "serve", "--host", "0.0.0.0", "--porta", "8080", "--dados", "/dados"]
