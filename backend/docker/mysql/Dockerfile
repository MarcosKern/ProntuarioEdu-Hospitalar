FROM mysql:8.4@sha256:a81d043930e51745522bd5c430961cf8286f0a23f0a9a2a6e0108f7ea71b0902 AS base

# O entrypoint oficial executa o DDL somente quando /var/lib/mysql está vazio.
COPY --chmod=0444 docs/database/prontuarioedu_mysql.sql /docker-entrypoint-initdb.d/10-prontuarioedu.sql
COPY --chmod=0555 docker/mysql/healthcheck.sh /usr/local/bin/prontuario-mysql-healthcheck

HEALTHCHECK --interval=5s --timeout=5s --start-period=60s --retries=20 \
    CMD ["/usr/local/bin/prontuario-mysql-healthcheck"]

FROM base AS test
COPY --chmod=0444 docker/mysql/20-test-database.sql /docker-entrypoint-initdb.d/20-test-database.sql

# O build padrão não inclui a criação do banco exclusivo da suíte.
FROM base AS development
