# Projeto Acadêmico — Programação Paralela (CCO085)
# Uso: make | make baseline | make openmp | make mpi | make clean

CXX ?= g++
MPICXX ?= mpic++
CXXFLAGS ?= -O2 -Wall -Wextra
OMPFLAGS ?= -fopenmp

BASELINE_SRC := baseline/04_convolucao.cpp
BASELINE_BIN := baseline/convolucao.out
OPENMP_SRC := openmp/04_convolucao_openmp.cpp
OPENMP_BIN := openmp/convolucao_openmp.out
MPI_SRC := mpi/04_convolucao_mpi.cpp
MPI_BIN := mpi/convolucao_mpi.out

.PHONY: all baseline openmp mpi clean check-final info help

all: baseline openmp mpi

baseline: $(BASELINE_BIN)

openmp:
	@if [ -f "$(OPENMP_SRC)" ]; then \
		$(MAKE) $(OPENMP_BIN); \
	else \
		echo "openmp: SKIPPED — fonte ausente: $(OPENMP_SRC)"; \
	fi

mpi:
	@if [ -f "$(MPI_SRC)" ]; then \
		$(MAKE) $(MPI_BIN); \
	else \
		echo "mpi: SKIPPED — fonte ausente: $(MPI_SRC)"; \
	fi

$(BASELINE_BIN): $(BASELINE_SRC)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(OPENMP_BIN): $(OPENMP_SRC)
	$(CXX) $(CXXFLAGS) $(OMPFLAGS) -o $@ $<

$(MPI_BIN): $(MPI_SRC)
	$(MPICXX) $(CXXFLAGS) -o $@ $<

# Use antes da entrega final: as três fontes precisam existir e compilar.
check-final:
	@test -f "$(BASELINE_SRC)" || { echo "Fonte ausente: $(BASELINE_SRC)"; exit 1; }
	@test -f "$(OPENMP_SRC)" || { echo "Fonte ausente: $(OPENMP_SRC)"; exit 1; }
	@test -f "$(MPI_SRC)" || { echo "Fonte ausente: $(MPI_SRC)"; exit 1; }
	@$(MAKE) all

info:
	@echo "CXX=$(CXX)"
	@echo "MPICXX=$(MPICXX)"
	@echo "CXXFLAGS=$(CXXFLAGS)"
	@echo "OMPFLAGS=$(OMPFLAGS)"
	@echo "Núcleos visíveis: $$(nproc)"

clean:
	rm -f $(BASELINE_BIN) $(OPENMP_BIN) $(MPI_BIN)

help:
	@echo "make             Compila todas as versões disponíveis"
	@echo "make baseline    Compila a versão sequencial"
	@echo "make openmp      Compila OpenMP, se a fonte existir"
	@echo "make mpi         Compila MPI, se a fonte existir"
	@echo "make check-final Falha se alguma das três fontes estiver ausente"
	@echo "make clean       Remove apenas executáveis gerados"
