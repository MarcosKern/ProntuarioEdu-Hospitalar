#!/bin/sh
set -eu

# TCP fica disponível após o entrypoint concluir os scripts de inicialização.
# As tabelas técnicas do Alembic não entram na contagem do domínio.
ready="$(MYSQL_PWD="$MYSQL_PASSWORD" mysql \
    --protocol=TCP --host=127.0.0.1 --user="$MYSQL_USER" \
    --database=prontuarioedu --batch --skip-column-names \
    --execute="SELECT
        (SELECT COUNT(*) FROM information_schema.tables
         WHERE table_schema=DATABASE() AND table_type='BASE TABLE'
         AND table_name REGEXP '^(cadastro|assistencial|clinico|cirurgia_maternidade|cme|auditoria)__') = 64
        AND (SELECT COUNT(*) FROM information_schema.table_constraints
         WHERE constraint_schema=DATABASE() AND constraint_type='FOREIGN KEY'
         AND table_name REGEXP '^(cadastro|assistencial|clinico|cirurgia_maternidade|cme|auditoria)__') = 121
        AND (SELECT COUNT(*) FROM information_schema.table_constraints
         WHERE constraint_schema=DATABASE() AND constraint_type='CHECK'
         AND table_name REGEXP '^(cadastro|assistencial|clinico|cirurgia_maternidade|cme|auditoria)__') = 40;" \
    2>/dev/null)" || exit 1

[ "$ready" = "1" ]
