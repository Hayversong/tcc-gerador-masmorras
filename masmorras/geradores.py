"""Ponto único de acesso aos geradores, usado pelos scripts de experimento."""
from __future__ import annotations

from .bsp import gerar_bsp
from .digger import gerar_digger
from .grade import Grade

ALGORITMOS = ("bsp", "digger")


def gerar(algoritmo: str, largura: int, altura: int, semente: int) -> tuple[Grade, dict]:
    """Gera uma masmorra. Retorna a grade e informações extras da execução."""
    if algoritmo == "bsp":
        return gerar_bsp(largura, altura, semente), {"atingiu_cobertura": 1, "passos": 0}
    if algoritmo == "digger":
        grade, r = gerar_digger(largura, altura, semente)
        return grade, {"atingiu_cobertura": int(r.atingiu_cobertura), "passos": r.passos}
    raise ValueError(f"algoritmo desconhecido: {algoritmo} (use: {', '.join(ALGORITMOS)})")
