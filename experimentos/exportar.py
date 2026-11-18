"""Gera uma masmorra e salva em JSON para carregar na Godot.

Exemplo:
    python -m experimentos.exportar --algoritmo bsp --largura 80 --altura 45 --semente 7 --saida mapa.json
"""
import argparse

from masmorras.exportacao import salvar_json
from masmorras.geradores import ALGORITMOS, gerar


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--algoritmo", choices=ALGORITMOS, required=True)
    ap.add_argument("--largura", type=int, default=80)
    ap.add_argument("--altura", type=int, default=45)
    ap.add_argument("--semente", type=int, default=0)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()

    grade, _ = gerar(a.algoritmo, a.largura, a.altura, a.semente)
    print("salvo em", salvar_json(grade, a.algoritmo, a.semente, a.saida))


if __name__ == "__main__":
    main()
