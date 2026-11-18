"""Confere implementações próprias contra bibliotecas de referência.

Só roda se SciPy, NumPy e NetworkX estiverem instalados; caso contrário,
os testes são pulados (o núcleo do projeto não depende dessas bibliotecas).
    pip install scipy numpy networkx
"""
import random
import unittest

from analise.analisar import mann_whitney, percentil
from masmorras.metricas import _pontes_e_articulacoes

try:
    import networkx as nx
    import numpy as np
    from scipy.stats import mannwhitneyu
    DISPONIVEL = True
except ImportError:  # pragma: no cover
    DISPONIVEL = False


@unittest.skipUnless(DISPONIVEL, "SciPy, NumPy ou NetworkX não instalados")
class TestConferenciaExterna(unittest.TestCase):
    def test_pontes_e_articulacoes_iguais_ao_networkx(self):
        rng = random.Random(0)
        for t in range(500):
            n = rng.randint(1, 40)
            g = nx.gnm_random_graph(n, rng.randint(0, 2 * n), seed=t)
            pontes, articulacoes = _pontes_e_articulacoes([list(g.neighbors(v)) for v in range(n)])
            with self.subTest(grafo=t):
                self.assertEqual(pontes, len(list(nx.bridges(g))))
                self.assertEqual(articulacoes, len(list(nx.articulation_points(g))))

    def test_mann_whitney_e_percentil_iguais_ao_scipy_numpy(self):
        rng = random.Random(1)
        for t in range(5):
            a = [rng.choice([0, 1, 2, 3, 3.5]) + rng.random() * (t % 2) for _ in range(300)]
            b = [rng.choice([0, 1, 2, 3, 4]) + rng.random() * (t % 2) for _ in range(250)]
            u, p = mann_whitney(a, b)
            ref = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic", use_continuity=True)
            with self.subTest(conjunto=t):
                self.assertAlmostEqual(u, float(ref.statistic), places=9)
                self.assertAlmostEqual(p, float(ref.pvalue), places=12)
                self.assertAlmostEqual(percentil(a, 0.95), float(np.percentile(a, 95)), places=9)


if __name__ == "__main__":
    unittest.main()
