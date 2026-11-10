# ADR 0007 — Codespaces e alinhamento integral a MySQL

Status: configuração de Codespaces solicitada; alinhamento MySQL confirmado explicitamente pelo responsável.

Dev Container oficial com Python 3.12, feature Docker in Docker e extensões declaradas para Python/Ruff, Postman, cliente MySQL e contêineres. Post-create instala o lock dev e preserva `.env` existente, sem importar SQL, executar migrações ou conectar automaticamente ao banco. Inicialização da API é ação separada, com encaminhamento de porta e hostname exato para Codespaces.

MySQL 8.4 externo é o único mecanismo suportado. Os quatro arquivos de requirements já usam PyMySQL, sem driver de outro mecanismo; não foram reescritos apenas para produzir mudança artificial. Retirado o ramo de dialeto legado da revisão técnica inicial, sem alterar o DDL que ela já executava no MySQL. Os documentos vigentes foram alinhados; histórico anterior permanece no Git.

A configuração foi lida pela CLI Dev Containers. Instalação real das extensões, build da feature e portas privadas precisam de um Codespace para validação final. O acesso ao Marketplace foi bloqueado na máquina atual; não se afirma que as extensões já tenham sido instaladas no GitHub.
