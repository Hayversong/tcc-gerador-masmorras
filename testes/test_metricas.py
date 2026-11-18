import unittest

from masmorras.grade import Grade, Sala
from masmorras.metricas import calcular


def _grade_duas_salas(ligadas: bool) -> Grade:
    g = Grade(12, 7)
    g.escavar_sala(Sala(1, 1, 3, 3))
    g.escavar_sala(Sala(8, 1, 3, 3))
    if ligadas:
        for x in range(4, 8):
            g.escavar(x, 2)
    return g


class TestMetricas(unittest.TestCase):
    def test_salas_desconectadas(self):
        m = calcular(_grade_duas_salas(ligadas=False))
        self.assertEqual(m["componentes_piso"], 2)
        self.assertEqual(m["totalmente_conectado"], 0)
        self.assertEqual(m["fracao_salas_alcancaveis"], 0.5)

    def test_salas_ligadas_por_corredor(self):
        m = calcular(_grade_duas_salas(ligadas=True))
        self.assertEqual(m["totalmente_conectado"], 1)
        self.assertEqual(m["regioes_sala"], 2)
        self.assertEqual(m["proporcao_corredor"], round(4 / 22, 4))
        self.assertEqual(m["ciclos"], 0)
        self.assertEqual(m["becos_sem_saida"], 0)
        # sala - corredor - sala: as duas ligações são pontes e o corredor é articulação
        self.assertEqual(m["pontes"], 2)
        self.assertEqual(m["fracao_pontes"], 1.0)
        self.assertEqual(m["pontos_articulacao"], 1)
        # centros das salas em (2, 2) e (9, 2): 7 passos
        self.assertEqual(m["distancia_media_salas"], 7)
        self.assertEqual(m["diametro_salas"], 7)

    def test_beco_sem_saida(self):
        g = Grade(10, 7)
        g.escavar_sala(Sala(1, 1, 3, 3))
        for x in range(4, 8):
            g.escavar(x, 2)
        self.assertEqual(calcular(g)["becos_sem_saida"], 1)

    def test_ciclo_entre_duas_salas(self):
        g = _grade_duas_salas(ligadas=True)
        # segundo corredor, por baixo, separado do primeiro
        for x in range(2, 10):
            g.escavar(x, 5)
        g.escavar(2, 4)
        g.escavar(9, 4)
        m = calcular(g)
        self.assertEqual(m["ciclos"], 1)
        # com dois caminhos, nenhuma ligação é crítica
        self.assertEqual(m["pontes"], 0)
        self.assertEqual(m["pontos_articulacao"], 0)

    def test_salas_sobrepostas_formam_uma_regiao(self):
        g = Grade(10, 8)
        g.escavar_sala(Sala(1, 1, 4, 4))
        g.escavar_sala(Sala(3, 3, 4, 4))
        m = calcular(g)
        self.assertEqual(m["pares_salas_sobrepostas"], 1)
        self.assertEqual(m["regioes_sala"], 1)


if __name__ == "__main__":
    unittest.main()
