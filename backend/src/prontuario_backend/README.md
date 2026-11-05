# Pacote do Back-end: MVC

- `models/`: dados, regras de negócio e persistência.
- `controllers/`: autenticação/autorização da operação e coordenação.
- `views/`: apresentação das respostas JSON e erros.
- `routes/`: URLs e métodos que apontam para Controllers.
- `config/`: inicialização, banco, segurança e Swagger.

Fluxo: rota → Controller → Model → Controller → View → resposta. A View não consulta o Model diretamente; o Controller passa o resultado que pode ser apresentado. Models não importam Controllers ou Views. Não há necessidade de interfaces de repositório ou composição por portas para cada funcionalidade.

São competências conceituais; a conexão exata depende do framework escolhido. Não há aplicação executável ainda.
