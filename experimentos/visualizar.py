"""Mostra uma masmorra no terminal e suas métricas.

Exemplo:
    python -m experimentos.visualizar --algoritmo digger --largura 80 --altura 45 --semente 7
"""
import argparse

from masmorras.geradores import ALGORITMOS, gerar
from masmorras.metricas import calcular


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--algoritmo", choices=ALGORITMOS, required=True)
    ap.add_argument("--largura", type=int, default=80)
    ap.add_argument("--altura", type=int, default=45)
    ap.add_argument("--semente", type=int, default=0)
    ap.add_argument("--sem-metricas", action="store_true")
    a = ap.parse_args()

    grade, extra = gerar(a.algoritmo, a.largura, a.altura, a.semente)
    print(grade)
    if not a.sem_metricas:
        for k, v in {**extra, **calcular(grade)}.items():
            print(f"{k:>26}: {v}")


if __name__ == "__main__":
    main()
