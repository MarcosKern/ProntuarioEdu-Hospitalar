-- ProntuárioEdu v2.0 | Referência física para MySQL 8.4 (InnoDB)
-- Modelo recebido e revisado para MySQL; 64 tabelas e 121 vínculos FK.
-- SQL para instalação inicial em banco vazio; DDL MySQL provoca commits implícitos.
-- Referência documental: não é uma migração Alembic nem deve ser importada automaticamente.
-- DATETIME(6) é armazenado em UTC por convenção da aplicação; ajustar conexão em UTC.
-- UUIDs mantidos como CHAR(36) ascii_bin (compatibilidade humana; não BINARY(16)).
-- Um banco MySQL com seis domínios por prefixo dominio__tabela; não são seis bancos separados.
-- Consulte README.md antes de planejar a instalação inicial; não contém cadastros ou seeds.

CREATE DATABASE IF NOT EXISTS `prontuarioedu`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `prontuarioedu`;
SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Unidade hospitalar, inclusive CME e ambulatório.

CREATE TABLE `cadastro__unidades` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(30) NOT NULL UNIQUE,
  nome VARCHAR(120) NOT NULL,
  tipo VARCHAR(40) NOT NULL,
  ativo TINYINT NOT NULL DEFAULT 1,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Leito identificado por unidade; código único dentro de uma unidade.

CREATE TABLE `cadastro__leitos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  unidade_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  codigo VARCHAR(30) NOT NULL,
  situacao VARCHAR(25) NOT NULL DEFAULT 'disponivel',
  UNIQUE(unidade_id,codigo),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Cadastro de pessoa atendida; não usar idade como dado definitivo.

CREATE TABLE `cadastro__pacientes` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  identificador VARCHAR(60) NOT NULL UNIQUE,
  nome VARCHAR(160) NOT NULL,
  nascimento DATE,
  sexo VARCHAR(30),
  ativo TINYINT NOT NULL DEFAULT 1,
  ficticio TINYINT NOT NULL DEFAULT 1,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Identidade do profissional, distinta de conta de acesso; estudantes com perfil `ALUNO_ENFERMAGEM` não precisam de registro profissional; esta tabela é opcional e reservada a atores habilitados quando cabível.

CREATE TABLE `cadastro__profissionais` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  nome VARCHAR(160) NOT NULL,
  categoria VARCHAR(40) NOT NULL,
  conselho VARCHAR(30),
  numero_registro VARCHAR(50),
  uf_registro CHAR(2),
  ativo TINYINT NOT NULL DEFAULT 1,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Credencial de acesso. Para login local, hash obrigatório (Argon2id recomendado), sem senha em texto claro.

CREATE TABLE `cadastro__usuarios` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  nome VARCHAR(160) NOT NULL,
  profissional_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  login VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_ci NOT NULL,
  email VARCHAR(150),
  hash_senha TEXT,
  provedor VARCHAR(40) NOT NULL DEFAULT 'local',
  ativo TINYINT NOT NULL DEFAULT 1,
  senha_alterada_em DATETIME(6),
  falhas_login INT NOT NULL DEFAULT 0,
  bloqueado_ate DATETIME(6),
  ultimo_login_em DATETIME(6),
  UNIQUE(login),
  CHECK (falhas_login >= 0),
  CHECK (provedor <> 'local' OR hash_senha IS NOT NULL),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Perfis iniciais `ADMINISTRADOR` (professor) e `ALUNO_ENFERMAGEM` (enfermeiro simulado), sem equivalência a habilitação profissional.

CREATE TABLE `cadastro__perfis` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(40) NOT NULL UNIQUE,
  descricao TEXT NOT NULL,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Catálogo de ações autorizáveis, por exemplo `PACIENTE_CONSULTAR`, `VITAIS_REGISTRAR`, `MAR_CHECAR`, `USUARIO_GERENCIAR`.

CREATE TABLE `cadastro__permissoes` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(100) NOT NULL UNIQUE,
  descricao TEXT,
  recurso VARCHAR(60) NOT NULL,
  acao VARCHAR(50) NOT NULL,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Relação N:N entre perfil e ação permitida; as restrições por alocação de paciente/atendimento são aplicadas adicionalmente para alunos.

CREATE TABLE `cadastro__perfil_permissao` (

  perfil_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  permissao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  PRIMARY KEY(perfil_id,permissao_id),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Atribuição histórica de perfil e escopo. Professor administrador pode ter escopo global ou de turma; o aluno não é autorizado por unidade. Seu escopo efetivo decorre de `alocacoes_pacientes` e, quando aplicável, `grupo_membros`. Unicidade entre atribuições ativas.

CREATE TABLE `cadastro__usuario_perfil` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  perfil_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  unidade_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  concedido_por CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  concedido_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  revogado_em DATETIME(6),
  CHECK(revogado_em IS NULL OR revogado_em >= concedido_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  chave_global_ativa TINYINT GENERATED ALWAYS AS (IF(revogado_em IS NULL AND unidade_id IS NULL, 1, NULL)) STORED,
  chave_unidade_ativa TINYINT GENERATED ALWAYS AS (IF(revogado_em IS NULL AND unidade_id IS NOT NULL, 1, NULL)) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Sessões revogáveis e rotação de credenciais de atualização; nunca persistir token em texto claro.

CREATE TABLE `cadastro__sessoes_usuario` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  refresh_token_hash VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
  expira_em DATETIME(6) NOT NULL,
  revogado_em DATETIME(6),
  ultimo_uso_em DATETIME(6),
  dispositivo_resumo VARCHAR(180),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Recuperação de senha por token de uso único e expiração curta.

CREATE TABLE `cadastro__recuperacoes_acesso` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  token_hash VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
  solicitado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  expira_em DATETIME(6) NOT NULL,
  usado_em DATETIME(6),
  CHECK(expira_em > solicitado_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Segundo fator, preferencialmente obrigatório para administradores. Segredos são cifrados; códigos de recuperação devem ser armazenados como hashes.

CREATE TABLE `cadastro__fatores_mfa` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  tipo VARCHAR(30) NOT NULL,
  segredo_criptografado TEXT,
  ativado_em DATETIME(6),
  revogado_em DATETIME(6),
  metadados JSON,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Turmas organizadas pelo professor/administrador, sem acesso clínico automático aos alunos.

CREATE TABLE `cadastro__turmas` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(50) NOT NULL UNIQUE,
  nome VARCHAR(120) NOT NULL,
  professor_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  periodo VARCHAR(40),
  status VARCHAR(20) NOT NULL DEFAULT 'ativa',
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Matrícula do aluno na turma, com histórico de saída e vínculo ativo único por par.

CREATE TABLE `cadastro__turma_alunos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  turma_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  aluno_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  ingressou_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  saiu_em DATETIME(6),
  status VARCHAR(20) NOT NULL DEFAULT 'ativo',
  CHECK(saiu_em IS NULL OR saiu_em >= ingressou_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  chave_ativa TINYINT GENERATED ALWAYS AS (IF(saiu_em IS NULL AND status = 'ativo', 1, NULL)) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Grupo de colaboração pertencente a uma turma.

CREATE TABLE `cadastro__grupos_trabalho` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  turma_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  nome VARCHAR(120) NOT NULL,
  criado_por CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ativo',
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Participação temporal do aluno no grupo; exige matrícula ativa na turma correspondente.

CREATE TABLE `cadastro__grupo_membros` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  grupo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  aluno_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  entrou_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  saiu_em DATETIME(6),
  status VARCHAR(20) NOT NULL DEFAULT 'ativo',
  CHECK(saiu_em IS NULL OR saiu_em >= entrou_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  chave_ativa TINYINT GENERATED ALWAYS AS (IF(saiu_em IS NULL AND status = 'ativo', 1, NULL)) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Episódio clínico: internação, pronto-socorro ou consulta; base de todos os registros.

CREATE TABLE `cadastro__atendimentos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  paciente_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  turma_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  unidade_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  contexto_atual_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  atendimento_origem_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  tipo_atendimento VARCHAR(30) NOT NULL,
  diagnostico_resumo TEXT,
  admissao_em DATETIME(6) NOT NULL,
  alta_em DATETIME(6),
  status VARCHAR(30) NOT NULL DEFAULT 'ativo',
  criado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  UNIQUE(id,paciente_id),
  CHECK(alta_em IS NULL OR alta_em >= admissao_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Linha do tempo de ocupações; o índice condicional limita ocupações abertas. Sobreposições históricas exigem validação transacional.

CREATE TABLE `cadastro__ocupacoes_leito` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  leito_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  inicio_em DATETIME(6) NOT NULL,
  fim_em DATETIME(6),
  CHECK(fim_em IS NULL OR fim_em > inicio_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  chave_atual TINYINT GENERATED ALWAYS AS (IF(fim_em IS NULL, 1, NULL)) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Autoriza **um aluno** OU **um grupo** a consultar/registrar no paciente e atendimento específico. Histórica, revogável, não apaga registros já feitos.

CREATE TABLE `cadastro__alocacoes_pacientes` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  paciente_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  aluno_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  grupo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  concedido_por CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  inicio_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  expira_em DATETIME(6),
  revogado_em DATETIME(6),
  motivo TEXT,
  CHECK((aluno_id IS NOT NULL) <> (grupo_id IS NOT NULL)),
  CHECK(expira_em IS NULL OR expira_em > inicio_em),
  CHECK(revogado_em IS NULL OR revogado_em >= inicio_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  chave_ativa TINYINT GENERATED ALWAYS AS (IF(revogado_em IS NULL, 1, NULL)) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Fluxos como internação enfermaria, pronto-socorro, UTI, consulta, maternidade e centro cirúrgico.

CREATE TABLE `assistencial__contextos_assistenciais` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(45) NOT NULL UNIQUE,
  nome VARCHAR(120) NOT NULL,
  tipo_atendimento VARCHAR(30) NOT NULL,
  nivel_cuidado VARCHAR(50),
  ativo TINYINT NOT NULL DEFAULT 1,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Catálogo único, SEM dose, posologia e registro de execução.

CREATE TABLE `assistencial__medicamentos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  nome VARCHAR(160) NOT NULL,
  principio_ativo VARCHAR(160),
  nome_comercial VARCHAR(160),
  forma_farmaceutica VARCHAR(80),
  descricao TEXT,
  ativo TINYINT NOT NULL DEFAULT 1,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Tabela intermediária N:N de disponibilidade e instrução; orientação padrão NÃO é registro de aplicação.

CREATE TABLE `assistencial__medicamento_contextos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  medicamento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  contexto_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  descricao_aplicacao_padrao TEXT,
  orientacao_operacional TEXT,
  habilitado TINYINT NOT NULL DEFAULT 1,
  versao INT NOT NULL DEFAULT 1,
  atualizado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE(medicamento_id,contexto_id,versao),
  CHECK(versao > 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Consulta agendada pode ou não gerar atendimento; nunca presume administração.

CREATE TABLE `assistencial__agendamentos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  paciente_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  professor_responsavel_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  unidade_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  inicio_previsto_em DATETIME(6) NOT NULL,
  fim_previsto_em DATETIME(6),
  status VARCHAR(30) NOT NULL,
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin UNIQUE,
  CHECK(fim_previsto_em IS NULL OR fim_previsto_em > inicio_previsto_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Histórico de mudança entre contextos; não substitui a ocupação de leito.

CREATE TABLE `assistencial__historico_contextos_atendimento` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  contexto_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  unidade_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  inicio_em DATETIME(6) NOT NULL,
  fim_em DATETIME(6),
  motivo TEXT,
  responsavel_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  CHECK(fim_em IS NULL OR fim_em > inicio_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Cabeçalho de ordem médica, intervenção de enfermagem ou cuidados. Assinatura e autorização são requisitos futuros.

CREATE TABLE `assistencial__prescricoes` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  contexto_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  autor_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  tipo VARCHAR(25) NOT NULL,
  modalidade VARCHAR(25) NOT NULL,
  status VARCHAR(25) NOT NULL DEFAULT 'rascunho',
  emitida_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  vigencia_inicio DATETIME(6),
  vigencia_fim DATETIME(6),
  assinada_em DATETIME(6),
  simulada TINYINT NOT NULL DEFAULT 1,
  CHECK(vigencia_fim IS NULL OR vigencia_inicio IS NULL OR vigencia_fim >= vigencia_inicio),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Item individual. Dose somente se necessária na ordem do paciente; não pertence ao catálogo.

CREATE TABLE `assistencial__prescricao_itens` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  prescricao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  medicamento_contexto_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  tipo_item VARCHAR(25) NOT NULL,
  descricao TEXT NOT NULL,
  dose VARCHAR(80),
  via VARCHAR(40),
  frequencia VARCHAR(50),
  observacoes TEXT,
  status VARCHAR(25) NOT NULL DEFAULT 'ativo',
  CHECK((tipo_item = 'medicamento' AND medicamento_contexto_id IS NOT NULL) OR (tipo_item <> 'medicamento' AND medicamento_contexto_id IS NULL)),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Ocorrência programada para horário completo; a internação utiliza agenda por turno.

CREATE TABLE `assistencial__aprazamentos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  previsto_em DATETIME(6) NOT NULL,
  status VARCHAR(25) NOT NULL DEFAULT 'agendado',
  origem_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  motivo TEXT,
  UNIQUE(item_id,previsto_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Log de decisões: administrado, omitido, suspenso, reaprazado ou retificação, sem sobrescrever eventos.

CREATE TABLE `assistencial__checagens_mar` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  aprazamento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  prescricao_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  usuario_executor_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  acao VARCHAR(30) NOT NULL,
  executada_em DATETIME(6) NOT NULL,
  observacao TEXT,
  registrada_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  retifica_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Evento simulado de administração, com descrição e autoria individual do estudante por `usuario_executor_id`. Somente administrações simuladas efetivas geram linha.

CREATE TABLE `assistencial__administracoes_medicamentos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  prescricao_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  aprazamento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  checagem_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin UNIQUE,
  contexto_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  usuario_executor_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  administrado_em DATETIME(6) NOT NULL,
  via_utilizada VARCHAR(50),
  descricao_aplicacao TEXT NOT NULL,
  observacoes TEXT,
  registrado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  retifica_administracao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  CHECK(CHAR_LENGTH(TRIM(descricao_aplicacao)) > 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Histórico de edições, assinaturas, substituições e suspensão de ordens.

CREATE TABLE `assistencial__historico_prescricao` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  prescricao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  acao VARCHAR(40) NOT NULL,
  dados_antes JSON,
  dados_depois JSON,
  usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  data_hora DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Evoluções, ocorrências, procedimentos, queixas e plantões.

CREATE TABLE `clinico__anotacoes` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  autor_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  tipo VARCHAR(40) NOT NULL,
  texto TEXT NOT NULL,
  registrada_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  retifica_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  CHECK(CHAR_LENGTH(TRIM(texto))>0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Série histórica de aferições. IMC é derivado de peso e altura.

CREATE TABLE `clinico__sinais_vitais` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  medido_em DATETIME(6) NOT NULL,
  pas DECIMAL(7,2),
  pad DECIMAL(7,2),
  fc DECIMAL(7,2),
  fr DECIMAL(7,2),
  temperatura DECIMAL(5,2),
  spo2 DECIMAL(5,2),
  glicemia DECIMAL(8,2),
  diurese DECIMAL(12,2),
  peso DECIMAL(8,2),
  altura DECIMAL(8,2),
  dor_num INT,
  observacoes TEXT,
  CHECK(spo2 IS NULL OR spo2 BETWEEN 0 AND 100),
  CHECK(dor_num IS NULL OR dor_num BETWEEN 0 AND 10),
  CHECK(peso IS NULL OR peso > 0),
  CHECK(altura IS NULL OR altura > 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Catálogo versionado de Glasgow, dor, RASS, Ramsay, Braden, Morse, NEWS etc.

CREATE TABLE `clinico__catalogo_escalas` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(40) NOT NULL,
  nome VARCHAR(120) NOT NULL,
  versao VARCHAR(30) NOT NULL,
  ativo TINYINT NOT NULL DEFAULT 1,
  UNIQUE(codigo,versao),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Cada preenchimento é um registro histórico independente.

CREATE TABLE `clinico__avaliacoes_escalas` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  escala_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  avaliada_em DATETIME(6) NOT NULL,
  score DECIMAL(8,2),
  classificacao VARCHAR(80),
  versao_criterios VARCHAR(30) NOT NULL,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Respostas que justificam a pontuação registrada.

CREATE TABLE `clinico__respostas_escalas` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  avaliacao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  criterio_codigo VARCHAR(80) NOT NULL,
  valor VARCHAR(80) NOT NULL,
  descricao TEXT,
  UNIQUE(avaliacao_id,criterio_codigo),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Episódio/avaliação suspeita de sepse; limites clínicos dependem de validação.

CREATE TABLE `clinico__protocolos_sepse` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  identificado_em DATETIME(6) NOT NULL,
  escala_spo2 VARCHAR(20),
  news2_pontos INT,
  lactato_inicial DECIMAL(8,2),
  foco TEXT,
  status VARCHAR(25) NOT NULL DEFAULT 'aberto',
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Medidas previstas por janela temporal do protocolo.

CREATE TABLE `clinico__sepse_bundles` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  protocolo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  janela_horas INT NOT NULL,
  criterio_codigo VARCHAR(80) NOT NULL,
  feito TINYINT NOT NULL DEFAULT 0,
  executado_em DATETIME(6),
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  CHECK(janela_horas > 0),
  UNIQUE(protocolo_id,janela_horas,criterio_codigo),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Cateteres, sondas, drenos, vias e dispositivos diversos.

CREATE TABLE `clinico__dispositivos_paciente` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  tipo VARCHAR(100) NOT NULL,
  local VARCHAR(120),
  calibre VARCHAR(50),
  instalado_em DATETIME(6) NOT NULL,
  troca_prevista_em DATETIME(6),
  removido_em DATETIME(6),
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  observacoes TEXT,
  CHECK(removido_em IS NULL OR removido_em >= instalado_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Entradas/saídas históricas; saldo é calculado por período.

CREATE TABLE `clinico__movimentos_hidricos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  direcao VARCHAR(10) NOT NULL,
  tipo VARCHAR(80) NOT NULL,
  volume_ml DECIMAL(12,2) NOT NULL,
  ocorrido_em DATETIME(6) NOT NULL,
  observacoes TEXT,
  retifica_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  CHECK(direcao IN ('entrada','saida')),
  CHECK(volume_ml > 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Procedimento vinculado a atendimento.

CREATE TABLE `cirurgia_maternidade__procedimentos_cirurgicos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  nome VARCHAR(180) NOT NULL,
  sala VARCHAR(50),
  inicio_em DATETIME(6),
  fim_em DATETIME(6),
  status VARCHAR(30) NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  CHECK(fim_em IS NULL OR inicio_em IS NULL OR fim_em >= inicio_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Modelos versionados para cirurgia e parto seguro.

CREATE TABLE `cirurgia_maternidade__modelos_checklist` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(60) NOT NULL,
  tipo VARCHAR(30) NOT NULL,
  versao VARCHAR(30) NOT NULL,
  ativo TINYINT NOT NULL DEFAULT 1,
  UNIQUE(codigo,versao),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Itens e fases de checklist.

CREATE TABLE `cirurgia_maternidade__itens_checklist` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  modelo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  fase VARCHAR(40) NOT NULL,
  codigo VARCHAR(60) NOT NULL,
  enunciado TEXT NOT NULL,
  ordem INT NOT NULL,
  obrigatorio TINYINT NOT NULL DEFAULT 1,
  UNIQUE(modelo_id,codigo),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Evento de nascimento vinculado ao atendimento materno.

CREATE TABLE `cirurgia_maternidade__partos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_mae_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  data_hora DATETIME(6),
  tipo VARCHAR(50),
  status VARCHAR(30) NOT NULL,
  observacoes TEXT,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Execução identificada, vinculável a cirurgia ou parto.

CREATE TABLE `cirurgia_maternidade__execucoes_checklist` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  modelo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  cirurgia_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  parto_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  responsavel_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  iniciada_em DATETIME(6) NOT NULL,
  concluida_em DATETIME(6),
  CHECK(NOT(cirurgia_id IS NOT NULL AND parto_id IS NOT NULL)),
  CHECK(concluida_em IS NULL OR concluida_em >= iniciada_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Registro das marcações do checklist com autoria.

CREATE TABLE `cirurgia_maternidade__respostas_checklist` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  execucao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  resposta VARCHAR(30) NOT NULL,
  respondida_em DATETIME(6) NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  observacao TEXT,
  UNIQUE(execucao_id,item_id),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- RN possui cadastro próprio como paciente; um parto pode ter vários RN.

CREATE TABLE `cirurgia_maternidade__recem_nascidos` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  parto_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  paciente_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
  ordem_nascimento INT NOT NULL,
  nascido_em DATETIME(6) NOT NULL,
  UNIQUE(parto_id,ordem_nascimento),
  CHECK(ordem_nascimento > 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Apgar de cada minuto avaliado, sem sobrescrever outro registro.

CREATE TABLE `cirurgia_maternidade__avaliacoes_apgar` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  rn_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  minuto_vida INT NOT NULL,
  aparencia INT NOT NULL,
  pulso INT NOT NULL,
  reflexo INT NOT NULL,
  atividade INT NOT NULL,
  respiracao INT NOT NULL,
  total INT NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  avaliado_em DATETIME(6) NOT NULL,
  CHECK(minuto_vida >= 0),
  CHECK(aparencia BETWEEN 0 AND 2 AND pulso BETWEEN 0 AND 2 AND reflexo BETWEEN 0 AND 2 AND atividade BETWEEN 0 AND 2 AND respiracao BETWEEN 0 AND 2),
  CHECK(total BETWEEN 0 AND 10),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Avaliação de idade gestacional, fórmula a validar clinicamente.

CREATE TABLE `cirurgia_maternidade__avaliacoes_capurro` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  rn_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  pele INT,
  orelha INT,
  mama INT,
  sulcos INT,
  total INT,
  ig_semanas DECIMAL(5,2),
  versao_criterios VARCHAR(30) NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  avaliado_em DATETIME(6) NOT NULL,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Cada teste/reteste do RN é histórico independente.

CREATE TABLE `cirurgia_maternidade__triagens_neonatais` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  rn_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  tipo_teste VARCHAR(60) NOT NULL,
  realizado TINYINT NOT NULL DEFAULT 0,
  coleta_em DATETIME(6),
  status VARCHAR(30) NOT NULL,
  resultado TEXT,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  dados_exame JSON,
  observacoes TEXT,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Cadastro de consumíveis e instrumentais.

CREATE TABLE `cme__materiais_cme` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(50) NOT NULL UNIQUE,
  nome VARCHAR(160) NOT NULL,
  categoria VARCHAR(70) NOT NULL,
  unidade_medida VARCHAR(20) NOT NULL,
  estoque_minimo DECIMAL(12,2) NOT NULL DEFAULT 0,
  ativo TINYINT NOT NULL DEFAULT 1,
  CHECK(estoque_minimo >= 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Livro de movimentos, independente de saldo atual.

CREATE TABLE `cme__movimentacoes_estoque_cme` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  material_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  tipo VARCHAR(20) NOT NULL,
  quantidade DECIMAL(12,2) NOT NULL,
  motivo TEXT,
  origem VARCHAR(100),
  destino VARCHAR(100),
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  ocorrida_em DATETIME(6) NOT NULL,
  CHECK(tipo IN ('entrada','saida','ajuste_entrada','ajuste_saida')),
  CHECK(quantidade > 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Modelo/referência de composição de kit.

CREATE TABLE `cme__kits_modelo` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(60) NOT NULL UNIQUE,
  nome VARCHAR(150) NOT NULL,
  ativo TINYINT NOT NULL DEFAULT 1,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Composição do modelo; FK composta e unicidade por material.

CREATE TABLE `cme__kit_modelo_itens` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  kit_modelo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  material_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  quantidade DECIMAL(12,2) NOT NULL,
  UNIQUE(kit_modelo_id,material_id),
  CHECK(quantidade > 0),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Cada kit físico possui rastreabilidade própria.

CREATE TABLE `cme__kits_instancias` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  kit_modelo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  identificador_rastreio VARCHAR(70) NOT NULL UNIQUE,
  etapa_atual VARCHAR(30) NOT NULL,
  status VARCHAR(30) NOT NULL,
  disponivel TINYINT NOT NULL DEFAULT 0,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Transições auditáveis entre as etapas.

CREATE TABLE `cme__movimentacoes_kit` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  kit_instancia_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  etapa_anterior VARCHAR(30),
  nova_etapa VARCHAR(30) NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  ocorrida_em DATETIME(6) NOT NULL,
  observacao TEXT,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Recebimento na área suja de materiais rastreados ou avulsos.

CREATE TABLE `cme__recebimentos_expurgo` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  kit_instancia_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  material_descricao TEXT,
  quantidade DECIMAL(12,2) NOT NULL,
  origem VARCHAR(120) NOT NULL,
  recebido_em DATETIME(6) NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  observacao TEXT,
  status VARCHAR(30) NOT NULL DEFAULT 'recebido',
  CHECK(quantidade > 0),
  CHECK(kit_instancia_id IS NOT NULL OR (material_descricao IS NOT NULL AND CHAR_LENGTH(TRIM(material_descricao))>0)),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Histórico de lavagem, inspeção e processamento.

CREATE TABLE `cme__eventos_expurgo` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  recebimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  status_anterior VARCHAR(30),
  status_novo VARCHAR(30) NOT NULL,
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  data_hora DATETIME(6) NOT NULL,
  observacao TEXT,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Equipamento da esterilização.

CREATE TABLE `cme__equipamentos_esterilizacao` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  codigo VARCHAR(50) NOT NULL UNIQUE,
  nome VARCHAR(120) NOT NULL,
  tipo VARCHAR(50) NOT NULL,
  ativo TINYINT NOT NULL DEFAULT 1,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Execução de ciclo, parâmetros e resultados.

CREATE TABLE `cme__ciclos_esterilizacao` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  equipamento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  numero_ciclo VARCHAR(50) NOT NULL,
  metodo VARCHAR(60) NOT NULL,
  temperatura_c DECIMAL(6,2),
  tempo_min DECIMAL(7,2),
  resultado_indicador VARCHAR(40),
  registrado_por_usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  iniciado_em DATETIME(6) NOT NULL,
  concluido_em DATETIME(6),
  observacoes TEXT,
  UNIQUE(equipamento_id,numero_ciclo),
  CHECK(concluido_em IS NULL OR concluido_em >= iniciado_em),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Carga associada ao ciclo de esterilização.

CREATE TABLE `cme__cargas_esterilizacao` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  ciclo_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  codigo_carga VARCHAR(60) NOT NULL,
  situacao VARCHAR(30) NOT NULL,
  UNIQUE(ciclo_id,codigo_carga),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Associação N:N entre carga e kits físicos.

CREATE TABLE `cme__carga_kits` (

  carga_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  kit_instancia_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  PRIMARY KEY(carga_id,kit_instancia_id),
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Trilha de operações com minimização de dados sensíveis e proteção contra alteração.

CREATE TABLE `auditoria__eventos_auditoria` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  entidade VARCHAR(100) NOT NULL,
  registro_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  acao VARCHAR(50) NOT NULL,
  antes JSON,
  depois JSON,
  ocorrido_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  ip_hash VARCHAR(128),
  correlacao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  justificativa TEXT,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Trilha de autenticação, falhas, bloqueios e saída sem registrar senhas ou tokens.

CREATE TABLE `auditoria__eventos_autenticacao` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  usuario_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  login_informado_hash TEXT,
  tipo_evento VARCHAR(60) NOT NULL,
  sucesso TINYINT NOT NULL,
  ocorrido_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  origem_resumo TEXT,
  sessao_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Metadados de arquivos; conteúdo guardado em repositório de objetos protegido.

CREATE TABLE `auditoria__anexos_documentais` (

  id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY DEFAULT (UUID()),
  atendimento_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
  tipo VARCHAR(60) NOT NULL,
  referencia VARCHAR(100) NOT NULL,
  nome VARCHAR(255) NOT NULL,
  mime VARCHAR(100) NOT NULL,
  hash_arquivo VARCHAR(128) NOT NULL,
  criado_por CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  objeto_chave TEXT NOT NULL,
  criado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Chaves estrangeiras: 121
ALTER TABLE `cadastro__leitos` ADD CONSTRAINT `fk_cadastro_leitos_35c3bfef18` FOREIGN KEY (unidade_id) REFERENCES `cadastro__unidades`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__usuarios` ADD CONSTRAINT `fk_cadastro_usuarios_6551c04334` FOREIGN KEY (profissional_id) REFERENCES `cadastro__profissionais`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__perfil_permissao` ADD CONSTRAINT `fk_cadastro_perfil_permissao_9d40354b78` FOREIGN KEY (perfil_id) REFERENCES `cadastro__perfis`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__perfil_permissao` ADD CONSTRAINT `fk_cadastro_perfil_permissao_a2c12e3155` FOREIGN KEY (permissao_id) REFERENCES `cadastro__permissoes`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__usuario_perfil` ADD CONSTRAINT `fk_cadastro_usuario_perfil_7b6aed7d94` FOREIGN KEY (usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__usuario_perfil` ADD CONSTRAINT `fk_cadastro_usuario_perfil_4621213856` FOREIGN KEY (perfil_id) REFERENCES `cadastro__perfis`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__usuario_perfil` ADD CONSTRAINT `fk_cadastro_usuario_perfil_7a6ded7285` FOREIGN KEY (unidade_id) REFERENCES `cadastro__unidades`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__usuario_perfil` ADD CONSTRAINT `fk_cadastro_usuario_perfil_6637ed8ac6` FOREIGN KEY (concedido_por) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__sessoes_usuario` ADD CONSTRAINT `fk_cadastro_sessoes_usuario_7cb9bff743` FOREIGN KEY (usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__recuperacoes_acesso` ADD CONSTRAINT `fk_cadastro_recuperacoes_acesso_51bb0696cf` FOREIGN KEY (usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__fatores_mfa` ADD CONSTRAINT `fk_cadastro_fatores_mfa_082e68a00d` FOREIGN KEY (usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__turmas` ADD CONSTRAINT `fk_cadastro_turmas_351f751be6` FOREIGN KEY (professor_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__turma_alunos` ADD CONSTRAINT `fk_cadastro_turma_alunos_9d2d5fe8da` FOREIGN KEY (turma_id) REFERENCES `cadastro__turmas`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__turma_alunos` ADD CONSTRAINT `fk_cadastro_turma_alunos_d64e485436` FOREIGN KEY (aluno_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__grupos_trabalho` ADD CONSTRAINT `fk_cadastro_grupos_trabalho_57afd00765` FOREIGN KEY (turma_id) REFERENCES `cadastro__turmas`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__grupos_trabalho` ADD CONSTRAINT `fk_cadastro_grupos_trabalho_f63a9420ef` FOREIGN KEY (criado_por) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__grupo_membros` ADD CONSTRAINT `fk_cadastro_grupo_membros_8a8c7edaa7` FOREIGN KEY (grupo_id) REFERENCES `cadastro__grupos_trabalho`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__grupo_membros` ADD CONSTRAINT `fk_cadastro_grupo_membros_4790b35fda` FOREIGN KEY (aluno_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__atendimentos` ADD CONSTRAINT `fk_cadastro_atendimentos_aab9b579b0` FOREIGN KEY (paciente_id) REFERENCES `cadastro__pacientes`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__atendimentos` ADD CONSTRAINT `fk_cadastro_atendimentos_5d48f83ce8` FOREIGN KEY (turma_id) REFERENCES `cadastro__turmas`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__atendimentos` ADD CONSTRAINT `fk_cadastro_atendimentos_3b4b29d81a` FOREIGN KEY (unidade_id) REFERENCES `cadastro__unidades`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__atendimentos` ADD CONSTRAINT `fk_cadastro_atendimentos_5b8f1aae47` FOREIGN KEY (contexto_atual_id) REFERENCES `assistencial__contextos_assistenciais`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__atendimentos` ADD CONSTRAINT `fk_cadastro_atendimentos_1c68a6d551` FOREIGN KEY (atendimento_origem_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__atendimentos` ADD CONSTRAINT `fk_cadastro_atendimentos_59025893ae` FOREIGN KEY (criado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__ocupacoes_leito` ADD CONSTRAINT `fk_cadastro_ocupacoes_leito_38f9c22157` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__ocupacoes_leito` ADD CONSTRAINT `fk_cadastro_ocupacoes_leito_045dd321e6` FOREIGN KEY (leito_id) REFERENCES `cadastro__leitos`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__alocacoes_pacientes` ADD CONSTRAINT `fk_cadastro_alocacoes_pacientes_f0034850fe` FOREIGN KEY (aluno_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__alocacoes_pacientes` ADD CONSTRAINT `fk_cadastro_alocacoes_pacientes_80655c0a57` FOREIGN KEY (grupo_id) REFERENCES `cadastro__grupos_trabalho`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__alocacoes_pacientes` ADD CONSTRAINT `fk_cadastro_alocacoes_pacientes_3912cbe037` FOREIGN KEY (concedido_por) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cadastro__alocacoes_pacientes` ADD CONSTRAINT `fk_cadastro_alocacoes_pacientes_4926cb48ec` FOREIGN KEY (atendimento_id,paciente_id) REFERENCES `cadastro__atendimentos`(id,paciente_id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__medicamento_contextos` ADD CONSTRAINT `fk_assistenc_medicamento_contexto_6c42c9b253` FOREIGN KEY (medicamento_id) REFERENCES `assistencial__medicamentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__medicamento_contextos` ADD CONSTRAINT `fk_assistenc_medicamento_contexto_173da04a16` FOREIGN KEY (contexto_id) REFERENCES `assistencial__contextos_assistenciais`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__agendamentos` ADD CONSTRAINT `fk_assistenc_agendamentos_866c089be1` FOREIGN KEY (paciente_id) REFERENCES `cadastro__pacientes`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__agendamentos` ADD CONSTRAINT `fk_assistenc_agendamentos_a65da16472` FOREIGN KEY (professor_responsavel_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__agendamentos` ADD CONSTRAINT `fk_assistenc_agendamentos_0689ec4dd7` FOREIGN KEY (unidade_id) REFERENCES `cadastro__unidades`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__agendamentos` ADD CONSTRAINT `fk_assistenc_agendamentos_bb2098dbde` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__historico_contextos_atendimento` ADD CONSTRAINT `fk_assistenc_historico_contextos__3a1e459299` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__historico_contextos_atendimento` ADD CONSTRAINT `fk_assistenc_historico_contextos__58201f3709` FOREIGN KEY (contexto_id) REFERENCES `assistencial__contextos_assistenciais`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__historico_contextos_atendimento` ADD CONSTRAINT `fk_assistenc_historico_contextos__bcfa7bdf10` FOREIGN KEY (unidade_id) REFERENCES `cadastro__unidades`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__historico_contextos_atendimento` ADD CONSTRAINT `fk_assistenc_historico_contextos__b4009546a0` FOREIGN KEY (responsavel_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__prescricoes` ADD CONSTRAINT `fk_assistenc_prescricoes_a673382818` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__prescricoes` ADD CONSTRAINT `fk_assistenc_prescricoes_1f936f4cf6` FOREIGN KEY (contexto_id) REFERENCES `assistencial__contextos_assistenciais`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__prescricoes` ADD CONSTRAINT `fk_assistenc_prescricoes_1404625bf2` FOREIGN KEY (autor_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__prescricao_itens` ADD CONSTRAINT `fk_assistenc_prescricao_itens_e4c1a6d70a` FOREIGN KEY (prescricao_id) REFERENCES `assistencial__prescricoes`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__prescricao_itens` ADD CONSTRAINT `fk_assistenc_prescricao_itens_d87af4bebb` FOREIGN KEY (medicamento_contexto_id) REFERENCES `assistencial__medicamento_contextos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__aprazamentos` ADD CONSTRAINT `fk_assistenc_aprazamentos_35c0e4ae56` FOREIGN KEY (item_id) REFERENCES `assistencial__prescricao_itens`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__aprazamentos` ADD CONSTRAINT `fk_assistenc_aprazamentos_49e0cbf864` FOREIGN KEY (origem_id) REFERENCES `assistencial__aprazamentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__checagens_mar` ADD CONSTRAINT `fk_assistenc_checagens_mar_1ad97db8bc` FOREIGN KEY (aprazamento_id) REFERENCES `assistencial__aprazamentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__checagens_mar` ADD CONSTRAINT `fk_assistenc_checagens_mar_22acdd2b9b` FOREIGN KEY (prescricao_item_id) REFERENCES `assistencial__prescricao_itens`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__checagens_mar` ADD CONSTRAINT `fk_assistenc_checagens_mar_29c885cb66` FOREIGN KEY (usuario_executor_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__checagens_mar` ADD CONSTRAINT `fk_assistenc_checagens_mar_f2b72dbb85` FOREIGN KEY (retifica_id) REFERENCES `assistencial__checagens_mar`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__administracoes_medicamentos` ADD CONSTRAINT `fk_assistenc_administracoes_medic_4d550da41c` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__administracoes_medicamentos` ADD CONSTRAINT `fk_assistenc_administracoes_medic_d7ae5104a5` FOREIGN KEY (prescricao_item_id) REFERENCES `assistencial__prescricao_itens`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__administracoes_medicamentos` ADD CONSTRAINT `fk_assistenc_administracoes_medic_bdd9b245b9` FOREIGN KEY (aprazamento_id) REFERENCES `assistencial__aprazamentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__administracoes_medicamentos` ADD CONSTRAINT `fk_assistenc_administracoes_medic_52abc3d687` FOREIGN KEY (checagem_id) REFERENCES `assistencial__checagens_mar`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__administracoes_medicamentos` ADD CONSTRAINT `fk_assistenc_administracoes_medic_2f2e46ea01` FOREIGN KEY (contexto_id) REFERENCES `assistencial__contextos_assistenciais`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__administracoes_medicamentos` ADD CONSTRAINT `fk_assistenc_administracoes_medic_14b06e99f9` FOREIGN KEY (usuario_executor_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__administracoes_medicamentos` ADD CONSTRAINT `fk_assistenc_administracoes_medic_9bc937624a` FOREIGN KEY (retifica_administracao_id) REFERENCES `assistencial__administracoes_medicamentos`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__historico_prescricao` ADD CONSTRAINT `fk_assistenc_historico_prescricao_72b15a16f4` FOREIGN KEY (prescricao_id) REFERENCES `assistencial__prescricoes`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__historico_prescricao` ADD CONSTRAINT `fk_assistenc_historico_prescricao_6402aa8b33` FOREIGN KEY (item_id) REFERENCES `assistencial__prescricao_itens`(id) ON DELETE RESTRICT;
ALTER TABLE `assistencial__historico_prescricao` ADD CONSTRAINT `fk_assistenc_historico_prescricao_cec6c7a437` FOREIGN KEY (usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__anotacoes` ADD CONSTRAINT `fk_clinico_anotacoes_0c80fc18b6` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__anotacoes` ADD CONSTRAINT `fk_clinico_anotacoes_68446f66cc` FOREIGN KEY (autor_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__anotacoes` ADD CONSTRAINT `fk_clinico_anotacoes_b2f7afe5ea` FOREIGN KEY (retifica_id) REFERENCES `clinico__anotacoes`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__sinais_vitais` ADD CONSTRAINT `fk_clinico_sinais_vitais_7d303087bf` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__sinais_vitais` ADD CONSTRAINT `fk_clinico_sinais_vitais_b310f9b8bc` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__avaliacoes_escalas` ADD CONSTRAINT `fk_clinico_avaliacoes_escalas_7a75046929` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__avaliacoes_escalas` ADD CONSTRAINT `fk_clinico_avaliacoes_escalas_60e736ebc6` FOREIGN KEY (escala_id) REFERENCES `clinico__catalogo_escalas`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__avaliacoes_escalas` ADD CONSTRAINT `fk_clinico_avaliacoes_escalas_248ca19558` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__respostas_escalas` ADD CONSTRAINT `fk_clinico_respostas_escalas_963887a173` FOREIGN KEY (avaliacao_id) REFERENCES `clinico__avaliacoes_escalas`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__protocolos_sepse` ADD CONSTRAINT `fk_clinico_protocolos_sepse_961080b415` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__protocolos_sepse` ADD CONSTRAINT `fk_clinico_protocolos_sepse_ed2396f563` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__sepse_bundles` ADD CONSTRAINT `fk_clinico_sepse_bundles_e597b9117a` FOREIGN KEY (protocolo_id) REFERENCES `clinico__protocolos_sepse`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__sepse_bundles` ADD CONSTRAINT `fk_clinico_sepse_bundles_6d28d48399` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__dispositivos_paciente` ADD CONSTRAINT `fk_clinico_dispositivos_pacient_62f90ba190` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__dispositivos_paciente` ADD CONSTRAINT `fk_clinico_dispositivos_pacient_cdbc01ec73` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__movimentos_hidricos` ADD CONSTRAINT `fk_clinico_movimentos_hidricos_a633dee5ee` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__movimentos_hidricos` ADD CONSTRAINT `fk_clinico_movimentos_hidricos_86e0538c01` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `clinico__movimentos_hidricos` ADD CONSTRAINT `fk_clinico_movimentos_hidricos_47e81d9a0b` FOREIGN KEY (retifica_id) REFERENCES `clinico__movimentos_hidricos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__procedimentos_cirurgicos` ADD CONSTRAINT `fk_cirurgia__procedimentos_cirurg_caf7266cf3` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__procedimentos_cirurgicos` ADD CONSTRAINT `fk_cirurgia__procedimentos_cirurg_b7ac2fcb7b` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__itens_checklist` ADD CONSTRAINT `fk_cirurgia__itens_checklist_10cebb4bed` FOREIGN KEY (modelo_id) REFERENCES `cirurgia_maternidade__modelos_checklist`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__partos` ADD CONSTRAINT `fk_cirurgia__partos_61e751ac16` FOREIGN KEY (atendimento_mae_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__partos` ADD CONSTRAINT `fk_cirurgia__partos_c9424ba23d` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__execucoes_checklist` ADD CONSTRAINT `fk_cirurgia__execucoes_checklist_bc0181135a` FOREIGN KEY (modelo_id) REFERENCES `cirurgia_maternidade__modelos_checklist`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__execucoes_checklist` ADD CONSTRAINT `fk_cirurgia__execucoes_checklist_33384c6d00` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__execucoes_checklist` ADD CONSTRAINT `fk_cirurgia__execucoes_checklist_28a96c3aa0` FOREIGN KEY (cirurgia_id) REFERENCES `cirurgia_maternidade__procedimentos_cirurgicos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__execucoes_checklist` ADD CONSTRAINT `fk_cirurgia__execucoes_checklist_78929884c4` FOREIGN KEY (parto_id) REFERENCES `cirurgia_maternidade__partos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__execucoes_checklist` ADD CONSTRAINT `fk_cirurgia__execucoes_checklist_0c04622503` FOREIGN KEY (responsavel_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__respostas_checklist` ADD CONSTRAINT `fk_cirurgia__respostas_checklist_66d51221cf` FOREIGN KEY (execucao_id) REFERENCES `cirurgia_maternidade__execucoes_checklist`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__respostas_checklist` ADD CONSTRAINT `fk_cirurgia__respostas_checklist_28fbd44007` FOREIGN KEY (item_id) REFERENCES `cirurgia_maternidade__itens_checklist`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__respostas_checklist` ADD CONSTRAINT `fk_cirurgia__respostas_checklist_a705c9c406` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__recem_nascidos` ADD CONSTRAINT `fk_cirurgia__recem_nascidos_42fee3994e` FOREIGN KEY (parto_id) REFERENCES `cirurgia_maternidade__partos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__recem_nascidos` ADD CONSTRAINT `fk_cirurgia__recem_nascidos_006c318d60` FOREIGN KEY (paciente_id) REFERENCES `cadastro__pacientes`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__avaliacoes_apgar` ADD CONSTRAINT `fk_cirurgia__avaliacoes_apgar_f6416e9e92` FOREIGN KEY (rn_id) REFERENCES `cirurgia_maternidade__recem_nascidos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__avaliacoes_apgar` ADD CONSTRAINT `fk_cirurgia__avaliacoes_apgar_1559578732` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__avaliacoes_capurro` ADD CONSTRAINT `fk_cirurgia__avaliacoes_capurro_c561cf8edf` FOREIGN KEY (rn_id) REFERENCES `cirurgia_maternidade__recem_nascidos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__avaliacoes_capurro` ADD CONSTRAINT `fk_cirurgia__avaliacoes_capurro_c6db30e3f9` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__triagens_neonatais` ADD CONSTRAINT `fk_cirurgia__triagens_neonatais_ea3ae16f36` FOREIGN KEY (rn_id) REFERENCES `cirurgia_maternidade__recem_nascidos`(id) ON DELETE RESTRICT;
ALTER TABLE `cirurgia_maternidade__triagens_neonatais` ADD CONSTRAINT `fk_cirurgia__triagens_neonatais_e1b2902cab` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__movimentacoes_estoque_cme` ADD CONSTRAINT `fk_cme_movimentacoes_estoqu_ecd3385b98` FOREIGN KEY (material_id) REFERENCES `cme__materiais_cme`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__movimentacoes_estoque_cme` ADD CONSTRAINT `fk_cme_movimentacoes_estoqu_1debaf6a86` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__kit_modelo_itens` ADD CONSTRAINT `fk_cme_kit_modelo_itens_33da4959b2` FOREIGN KEY (kit_modelo_id) REFERENCES `cme__kits_modelo`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__kit_modelo_itens` ADD CONSTRAINT `fk_cme_kit_modelo_itens_6b621d59d5` FOREIGN KEY (material_id) REFERENCES `cme__materiais_cme`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__kits_instancias` ADD CONSTRAINT `fk_cme_kits_instancias_3c2586f314` FOREIGN KEY (kit_modelo_id) REFERENCES `cme__kits_modelo`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__movimentacoes_kit` ADD CONSTRAINT `fk_cme_movimentacoes_kit_02ddffdfad` FOREIGN KEY (kit_instancia_id) REFERENCES `cme__kits_instancias`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__movimentacoes_kit` ADD CONSTRAINT `fk_cme_movimentacoes_kit_dd11fa4d4a` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__recebimentos_expurgo` ADD CONSTRAINT `fk_cme_recebimentos_expurgo_1dc8aea45b` FOREIGN KEY (kit_instancia_id) REFERENCES `cme__kits_instancias`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__recebimentos_expurgo` ADD CONSTRAINT `fk_cme_recebimentos_expurgo_e40c8d40fc` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__eventos_expurgo` ADD CONSTRAINT `fk_cme_eventos_expurgo_222d17fe52` FOREIGN KEY (recebimento_id) REFERENCES `cme__recebimentos_expurgo`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__eventos_expurgo` ADD CONSTRAINT `fk_cme_eventos_expurgo_7bde651ecb` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__ciclos_esterilizacao` ADD CONSTRAINT `fk_cme_ciclos_esterilizacao_968a848ab5` FOREIGN KEY (equipamento_id) REFERENCES `cme__equipamentos_esterilizacao`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__ciclos_esterilizacao` ADD CONSTRAINT `fk_cme_ciclos_esterilizacao_1bfaf1b672` FOREIGN KEY (registrado_por_usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__cargas_esterilizacao` ADD CONSTRAINT `fk_cme_cargas_esterilizacao_c14d7c9c2c` FOREIGN KEY (ciclo_id) REFERENCES `cme__ciclos_esterilizacao`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__carga_kits` ADD CONSTRAINT `fk_cme_carga_kits_26602aa446` FOREIGN KEY (carga_id) REFERENCES `cme__cargas_esterilizacao`(id) ON DELETE RESTRICT;
ALTER TABLE `cme__carga_kits` ADD CONSTRAINT `fk_cme_carga_kits_df7cdadc91` FOREIGN KEY (kit_instancia_id) REFERENCES `cme__kits_instancias`(id) ON DELETE RESTRICT;
ALTER TABLE `auditoria__eventos_auditoria` ADD CONSTRAINT `fk_auditoria_eventos_auditoria_02f547b892` FOREIGN KEY (usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `auditoria__eventos_autenticacao` ADD CONSTRAINT `fk_auditoria_eventos_autenticacao_033fa52d0a` FOREIGN KEY (usuario_id) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;
ALTER TABLE `auditoria__eventos_autenticacao` ADD CONSTRAINT `fk_auditoria_eventos_autenticacao_146e28c646` FOREIGN KEY (sessao_id) REFERENCES `cadastro__sessoes_usuario`(id) ON DELETE RESTRICT;
ALTER TABLE `auditoria__anexos_documentais` ADD CONSTRAINT `fk_auditoria_anexos_documentais_d3bab9a7e9` FOREIGN KEY (atendimento_id) REFERENCES `cadastro__atendimentos`(id) ON DELETE RESTRICT;
ALTER TABLE `auditoria__anexos_documentais` ADD CONSTRAINT `fk_auditoria_anexos_documentais_af09ab5fd6` FOREIGN KEY (criado_por) REFERENCES `cadastro__usuarios`(id) ON DELETE RESTRICT;

-- Indices e unicidades condicionais
-- uq_usuarios_login_lower: dispensado; UNIQUE(login) + collation utf8mb4_0900_as_ci asseguram login sem distinguir maiúsculas.
CREATE UNIQUE INDEX `uq_usuario_perfil_global_ativo` ON `cadastro__usuario_perfil` (usuario_id, perfil_id, chave_global_ativa);
CREATE UNIQUE INDEX `uq_usuario_perfil_unidade_ativo` ON `cadastro__usuario_perfil` (usuario_id, perfil_id, unidade_id, chave_unidade_ativa);
CREATE UNIQUE INDEX `uq_turma_aluno_ativo` ON `cadastro__turma_alunos` (turma_id,aluno_id, chave_ativa);
CREATE UNIQUE INDEX `uq_grupo_membro_ativo` ON `cadastro__grupo_membros` (grupo_id,aluno_id, chave_ativa);
CREATE UNIQUE INDEX `uq_alocacao_individual_ativa` ON `cadastro__alocacoes_pacientes` (atendimento_id,aluno_id, chave_ativa);
CREATE UNIQUE INDEX `uq_alocacao_grupo_ativa` ON `cadastro__alocacoes_pacientes` (atendimento_id,grupo_id, chave_ativa);
CREATE INDEX `ix_alocacao_aluno_atendimento` ON `cadastro__alocacoes_pacientes` (aluno_id,atendimento_id,inicio_em, revogado_em);
CREATE INDEX `ix_alocacao_grupo_atendimento` ON `cadastro__alocacoes_pacientes` (grupo_id,atendimento_id,inicio_em, revogado_em);
CREATE INDEX `ix_aluno_grupos` ON `cadastro__grupo_membros` (aluno_id,grupo_id, saiu_em);
CREATE INDEX `ix_atendimento_paciente` ON `cadastro__atendimentos` (paciente_id,admissao_em DESC);
CREATE INDEX `ix_atendimento_turma` ON `cadastro__atendimentos` (turma_id,status);
CREATE INDEX `ix_atendimento_unidade` ON `cadastro__atendimentos` (unidade_id,status);
CREATE UNIQUE INDEX `uq_leito_atual` ON `cadastro__ocupacoes_leito` (leito_id, chave_atual);
CREATE UNIQUE INDEX `uq_atendimento_leito_atual` ON `cadastro__ocupacoes_leito` (atendimento_id, chave_atual);
CREATE INDEX `ix_prescricao_atendimento` ON `assistencial__prescricoes` (atendimento_id,status,vigencia_inicio);
CREATE INDEX `ix_medicamento_contexto` ON `assistencial__medicamento_contextos` (contexto_id,habilitado,medicamento_id);
CREATE INDEX `ix_aprazamento_horario` ON `assistencial__aprazamentos` (previsto_em,status);
CREATE INDEX `ix_aprazamento_item` ON `assistencial__aprazamentos` (item_id,previsto_em);
CREATE INDEX `ix_checagem_item` ON `assistencial__checagens_mar` (prescricao_item_id,executada_em DESC);
CREATE INDEX `ix_administracao_atendimento` ON `assistencial__administracoes_medicamentos` (atendimento_id,administrado_em DESC);
CREATE INDEX `ix_vitais_atendimento` ON `clinico__sinais_vitais` (atendimento_id,medido_em DESC);
CREATE INDEX `ix_anotacao_atendimento` ON `clinico__anotacoes` (atendimento_id,registrada_em DESC);
CREATE INDEX `ix_escala_atendimento` ON `clinico__avaliacoes_escalas` (atendimento_id,avaliada_em DESC);
CREATE INDEX `ix_balanco_atendimento` ON `clinico__movimentos_hidricos` (atendimento_id,ocorrido_em DESC);
CREATE INDEX `ix_sepses_atendimento` ON `clinico__protocolos_sepse` (atendimento_id,identificado_em DESC);
CREATE INDEX `ix_kit_historico` ON `cme__movimentacoes_kit` (kit_instancia_id,ocorrida_em DESC);
CREATE INDEX `ix_expurgo_historico` ON `cme__eventos_expurgo` (recebimento_id,data_hora DESC);
CREATE INDEX `ix_estoque_movimentos` ON `cme__movimentacoes_estoque_cme` (material_id,ocorrida_em DESC);
CREATE INDEX `ix_auditoria_recurso` ON `auditoria__eventos_auditoria` (entidade,registro_id,ocorrido_em DESC);
CREATE INDEX `ix_auditoria_usuario` ON `auditoria__eventos_auditoria` (usuario_id,ocorrido_em DESC);
-- REGRAS QUE NÃO SÃO GARANTIDAS APENAS POR DDL:
-- 1. Validar autorização de aluno no atendimento por alocação individual ou grupo ativo,
--    antes de QUALQUER leitura/escrita (inclusive downloads e relatórios).
-- 2. Impedir sobreposição histórica de ocupações do mesmo leito em intervalos diferentes.
-- 3. Relacionar de forma coerente IDs atendimento/paciente, prescricao/contexto e RN/mãe.
-- 4. Verificar assinatura/autoria e permissões por operação/visibilidade.
-- 5. Operar saldo de estoque em transação com lock para impedir saldo negativo concorrente.
-- 6. Preservar retificações, auditoria e histórico MAR sem UPDATE/DELETE indevidos.
-- A autorização por registro deve ser aplicada no backend; FKs não validam acesso do usuário.
