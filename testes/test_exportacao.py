import json
import tempfile
import unittest
from pathlib import Path

from masmorras.bsp import gerar_bsp
from masmorras.exportacao import salvar_json


class TestExportacao(unittest.TestCase):
    def test_formato_lido_pela_godot(self):
        grade = gerar_bsp(40, 30, 5)
        with tempfile.TemporaryDirectory() as tmp:
            caminho = salvar_json(grade, "bsp", 5, Path(tmp) / "mapa.json")
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        self.assertEqual((dados["largura"], dados["altura"]), (40, 30))
        self.assertEqual(len(dados["linhas"]), 30)
        self.assertTrue(all(len(l) == 40 and set(l) <= {"0", "1"} for l in dados["linhas"]))
        self.assertEqual(sum(l.count("1") for l in dados["linhas"]), grade.total_piso())
        x, y = dados["inicio"]
        self.assertEqual(dados["linhas"][y][x], "1")  # jogador começa no piso
        self.assertEqual(len(dados["salas"]), len(grade.salas))


if __name__ == "__main__":
    unittest.main()
