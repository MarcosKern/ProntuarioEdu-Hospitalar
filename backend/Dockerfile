# Python 3.12.16 on Alpine 3.23, pinned to the verified upstream manifest.
# Refresh the digest regularly and scan the complete image before merging.
FROM python:3.12-alpine3.23@sha256:9a7b46da82fe49a9118e0aa7e35ac3b831aa53ad4f4ebf3e16654732bc958a62
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
# Correção publicada no Alpine 3.23-stable; o build falha se o pacote não puder ser instalado.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    apk add --no-cache --upgrade krb5-libs=1.22.3-r0
COPY requirements.txt ./
# CA opcional fornecida por BuildKit para ambientes com proxy corporativo.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    python -m pip install --no-cache-dir -r requirements.txt
RUN adduser -D -u 1000 app
COPY --chown=app:app src ./src
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app scripts/create_admin.py ./scripts/create_admin.py
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["python", "-m", "uvicorn", "prontuario_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-proxy-headers"]
