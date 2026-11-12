"""Verifica rejeição de resultados inválidos e geração das curvas sem MPI."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
from script_analise import curva, executar


class AnaliseTest(unittest.TestCase):
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
