FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.txt ./
# CA opcional fornecida por BuildKit para ambientes com proxy corporativo.
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    python -m pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home app && mkdir -p /app/data && chown app:app /app/data
COPY --chown=app:app src ./src
USER app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "prontuario_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
