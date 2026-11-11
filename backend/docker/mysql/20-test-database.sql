-- Executado somente pelo Compose de testes, após o schema de domínio.
-- A suíte destrutiva usa um database separado daquele consultado pela API.
CREATE DATABASE IF NOT EXISTS `prontuario_test`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
GRANT ALL PRIVILEGES ON `prontuario_test`.* TO 'prontuario_test'@'%';
