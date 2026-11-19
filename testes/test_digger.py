import unittest

from masmorras.digger import ParametrosDigger, gerar_digger
from masmorras.metricas import calcular

GRADES = ((40, 30), (80, 45), (160, 90))


class TestDigger(unittest.TestCase):
    def test_mesma_semente_mesmo_mapa(self):
        a, _ = gerar_digger(80, 45, 3)
        b, _ = gerar_digger(80, 45, 3)
        self.assertEqual(str(a), str(b))

    def test_comeca_no_centro(self):
        g, _ = gerar_digger(40, 30, 0)
        self.assertTrue(g.eh_piso(20, 15))

    def test_atinge_cobertura_e_fica_conectado(self):
        for largura, altura in GRADES:
            for semente in range(50):
                with self.subTest(grade=(largura, altura), semente=semente):
                    g, r = gerar_digger(largura, altura, semente)
                    self.assertTrue(r.atingiu_cobertura)
                    self.assertGreaterEqual(g.total_piso(), int(0.35 * largura * altura))
                    self.assertEqual(calcular(g)["totalmente_conectado"], 1)

    def test_grade_minima_nao_quebra(self):
        g, r = gerar_digger(3, 3, 0)
        self.assertTrue(g.eh_piso(1, 1))
        self.assertFalse(r.atingiu_cobertura)

    def test_teto_de_passos(self):
        p = ParametrosDigger(cobertura_alvo=0.99, fator_teto_passos=1)
        g, r = gerar_digger(40, 30, 0, p)
        self.assertFalse(r.atingiu_cobertura)
        self.assertEqual(r.passos, 40 * 30)


if __name__ == "__main__":
    unittest.main()
