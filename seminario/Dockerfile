# Mesmo sistema-base e ferramentas de compilação do ambiente oficial CCO085.
# Git é incluído para o controle de versão funcionar no Dev Container.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gdb \
        git \
        valgrind \
        libomp-dev \
        openmpi-bin \
        libopenmpi-dev \
        python3 \
        python3-pip \
        time \
        nano \
        less \
        ca-certificates \
    && git config --system --add safe.directory /workspace \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab
CMD ["/bin/bash"]
