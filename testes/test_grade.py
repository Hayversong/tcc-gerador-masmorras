import unittest

from masmorras.grade import PAREDE, PISO, Grade, Sala


class TestGrade(unittest.TestCase):
    def test_comeca_toda_parede(self):
        g = Grade(10, 8)
        self.assertEqual(g.total_piso(), 0)

    def test_borda_nunca_e_escavada(self):
        g = Grade(10, 8)
        self.assertFalse(g.escavar(0, 3))
        self.assertFalse(g.escavar(9, 3))
        self.assertEqual(g.obter(0, 3), PAREDE)

    def test_escavar_sala(self):
        g = Grade(10, 8)
        novas = g.escavar_sala(Sala(2, 2, 3, 2))
        self.assertEqual(novas, 6)
        self.assertEqual(g.obter(4, 3), PISO)
        self.assertEqual(len(g.salas), 1)

    def test_sobreposicao_de_salas(self):
        self.assertTrue(Sala(1, 1, 3, 3).sobrepoe(Sala(3, 3, 2, 2)))
        self.assertFalse(Sala(1, 1, 3, 3).sobrepoe(Sala(4, 1, 2, 2)))


if __name__ == "__main__":
    unittest.main()
