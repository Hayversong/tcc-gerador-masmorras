import unittest

from masmorras.bsp import gerar_bsp
from masmorras.metricas import calcular

GRADES = ((40, 30), (80, 45), (160, 90))


class TestBSP(unittest.TestCase):
    def test_mesma_semente_mesmo_mapa(self):
        self.assertEqual(str(gerar_bsp(80, 45, 3)), str(gerar_bsp(80, 45, 3)))

    def test_sementes_diferentes_mapas_diferentes(self):
        self.assertNotEqual(str(gerar_bsp(80, 45, 3)), str(gerar_bsp(80, 45, 4)))

    def test_sempre_conectado_e_sem_sobreposicao(self):
        for largura, altura in GRADES:
            for semente in range(100):
                with self.subTest(grade=(largura, altura), semente=semente):
                    m = calcular(gerar_bsp(largura, altura, semente))
                    self.assertEqual(m["totalmente_conectado"], 1)
                    self.assertEqual(m["pares_salas_sobrepostas"], 0)

    def test_parametros_incompativeis_dao_erro_claro(self):
        from masmorras.bsp import ParametrosBSP
        with self.assertRaisesRegex(ValueError, "folha_minima"):
            gerar_bsp(40, 30, 0, ParametrosBSP(folha_minima=4))
        with self.assertRaisesRegex(ValueError, "pequena demais"):
            gerar_bsp(5, 5, 0)

    def test_borda_e_parede(self):
        g = gerar_bsp(40, 30, 1)
        linhas = g.linhas()
        self.assertTrue(set(linhas[0]) == set(linhas[-1]) == {"#"})
        self.assertTrue(all(l[0] == "#" and l[-1] == "#" for l in linhas))


if __name__ == "__main__":
    unittest.main()
