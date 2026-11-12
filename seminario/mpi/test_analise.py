"""Verifica rejeição de resultados inválidos e geração das curvas sem MPI."""
import subprocess
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
from script_analise import curva, executar, gerar_graficos
import script_medicao as medicao
from dataclasses import replace


class AnaliseTest(unittest.TestCase):
    @patch.object(medicao.os, 'cpu_count', return_value=8)
    @patch.object(medicao.subprocess, 'run')
    def test_filtra_slots_mpi_sem_oversubscribe(self, run, cpu_count):
        run.side_effect = [subprocess.CompletedProcess([], 0, '', '') for _ in range(3)] + [
            subprocess.CompletedProcess([], 1, '', 'There are not enough slots available')]
        with patch.object(medicao.os, 'sched_getaffinity', return_value=set(range(8)), create=True):
            self.assertEqual(medicao.unidades_disponiveis(medicao.IMPLEMENTACOES[-1], True), (1, 2, 4))
        self.assertEqual(run.call_count, 4)

    def test_graficos_rejeitam_campanha_incompleta(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / 'dados').mkdir()
            (raiz / 'dados/.campanha_em_andamento').touch()
            with self.assertRaisesRegex(RuntimeError, 'Campanha incompleta'):
                gerar_graficos(raiz)

    def test_campanha_padronizada_e_graficos(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            implementacoes = tuple(replace(i, fonte=raiz / i.nome / i.fonte.name,
                                           executavel=raiz / i.nome / i.executavel.name)
                                   for i in medicao.IMPLEMENTACOES if i.nome != 'openmp')
            for i in implementacoes:
                i.fonte.parent.mkdir()

            def simular(comando, **kwargs):
                mpi = comando[0] == 'mpirun'
                n, passes = comando[-3:-1] if mpi else comando[-2:]
                tempo = 1 if mpi else 2
                return subprocess.CompletedProcess(comando, 0,
                    f'N={n} passes={passes} checksum=123.00 tempo={tempo}.000000 s\n',
                    'validacao=OK\ncomunicacao_s=0.1 computacao_s=0.8\n' if mpi else '')

            with (patch.object(medicao, 'RAIZ_PROJETO', raiz),
                  patch.object(medicao, 'DIRETORIO_DADOS_COMPARTILHADOS', raiz / 'dados'),
                  patch.object(medicao, 'IMPLEMENTACOES', implementacoes),
                  patch.object(medicao, 'TAMANHOS_MATRIZ', (5,)),
                  patch.object(medicao, 'REPETICOES', 2),
                  patch.object(medicao, 'unidades_disponiveis', return_value=(1,)),
                  patch.object(medicao, 'preparar_implementacao', return_value=None),
                  patch.object(medicao.subprocess, 'run', side_effect=simular)):
                medicao.executar_campanha()
            for nome, colunas in [('mpi/dados/mpi_medicoes.csv', medicao.COLUNAS_MEDICOES),
                                  ('mpi/dados/mpi_resumo.csv', medicao.COLUNAS_RESUMO),
                                  ('dados/metricas.csv', medicao.COLUNAS_METRICAS)]:
                with (raiz / nome).open(newline='', encoding='utf-8') as f:
                    self.assertEqual(tuple(csv.DictReader(f).fieldnames), colunas)
            with (raiz / 'dados/metricas.csv').open(newline='', encoding='utf-8') as f:
                mpi = [l for l in csv.DictReader(f) if l['implementacao'] == 'mpi'][0]
                self.assertEqual(float(mpi['speedup']), 2)
            gerar_graficos(raiz)
            self.assertEqual(len(list((raiz / 'mpi/graficos').glob('*.svg'))), 4)
            self.assertFalse((raiz / 'mpi/dados/analise_medicoes.csv').exists())
            # Um arquivo truncado não pode produzir gráficos aparentemente completos.
            caminho = raiz / 'baseline/dados/baseline_medicoes.csv'
            linhas = caminho.read_text(encoding='utf-8').splitlines()
            caminho.write_text('\n'.join(linhas[:-1]) + '\n', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'CSV incompleto'):
                gerar_graficos(raiz)

    def resultado(self, stderr='validacao=OK\ncomunicacao_s=0.01 computacao_s=0.02\n'):
        return subprocess.CompletedProcess([], 0,
            'N=5 passes=3 checksum=123.00 tempo=0.030000 s\n', stderr)

    @patch('script_analise.subprocess.run')
    def test_tempos_e_validacao(self, run):
        run.return_value = self.resultado()
        self.assertEqual(executar([], 5, 3, True), ('123.00', .03, .01, .02))

    @patch('script_analise.subprocess.run')
    def test_rejeita_validacao_ausente_ou_falha(self, run):
        for stderr in ('', 'validacao=FALHOU\n'):
            run.return_value = self.resultado(stderr)
            with self.assertRaises(RuntimeError):
                executar([], 5, 3, True)

    @patch('script_analise.subprocess.run')
    def test_rejeita_parametros_divergentes(self, run):
        run.return_value = self.resultado()
        with self.assertRaises(RuntimeError):
            executar([], 6, 3, True)

    @patch('script_analise.subprocess.run')
    def test_propaga_falha_do_programa(self, run):
        run.side_effect = subprocess.CalledProcessError(2, ['mpi'])
        with self.assertRaises(subprocess.CalledProcessError):
            executar([], 5, 3, True)

    def test_svg_com_varias_series_e_um_processo(self):
        linhas = [dict(n=n, processos=1, speedup=0.5) for n in (3, 5)]
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'curva.svg'
            curva(caminho, linhas, 'speedup', 'Speedup', lambda p: p)
            raiz = ET.parse(caminho).getroot()
            ns = {'s': 'http://www.w3.org/2000/svg'}
            self.assertEqual(len(raiz.findall('s:polyline', ns)), 2)
            self.assertEqual(len(raiz.findall('s:circle', ns)), 2)


if __name__ == '__main__':
    unittest.main()
