FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

USER root
# A imagem inclui uma fonte APT do Yarn cuja chave pode estar desatualizada.
# Yarn não é dependência deste ambiente; remova a fonte antes das features Docker.
# As demais fontes e a verificação de assinaturas do APT permanecem habilitadas.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn.sources
