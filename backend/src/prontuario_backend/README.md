# Pacote do Back-end: MVC

- `models/`: dados, regras de negócio e persistência.
- `controllers/`: autenticação/autorização da operação e coordenação.
- `views/`: apresentação das respostas JSON e erros.
- `routes/`: URLs e métodos que apontam para Controllers.
- `config/`: inicialização, banco, segurança e Swagger.

Fluxo: rota → Controller → Model → Controller → View → resposta. A View não consulta o Model diretamente; o Controller passa o resultado que pode ser apresentado. Models não importam Controllers ou Views. Não há necessidade de interfaces de repositório ou composição por portas para cada funcionalidade.

A aplicação FastAPI está em `main.py`. O fluxo executável `/health` passa por rota, Controller, Model e View e verifica SQL. `/api/v1/me` demonstra a identificação por token. Veja a instalação e execução no README do Back-end.
