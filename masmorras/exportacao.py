"""Exportação de masmorras em JSON para uso na Godot Engine (integração opção A).

Formato:
{
  "versao": 1,
  "algoritmo": "bsp",
  "semente": 7,
  "largura": 80,
  "altura": 45,
  "linhas": ["0000...", "0111...", ...],   # uma string por linha; 0 = parede, 1 = piso
  "salas": [{"x": 3, "y": 2, "largura": 4, "altura": 5}, ...],
  "inicio": [x, y]                         # célula sugerida para o jogador
}
"""
from __future__ import annotations

import json
from pathlib import Path

from .grade import Grade


def para_dict(grade: Grade, algoritmo: str, semente: int) -> dict:
    if grade.salas:
        inicio = list(grade.salas[0].centro)
    else:
        i = grade.celulas.index(1)
        inicio = [i % grade.largura, i // grade.largura]
    return {
        "versao": 1,
        "algoritmo": algoritmo,
        "semente": semente,
        "largura": grade.largura,
        "altura": grade.altura,
        "linhas": grade.linhas(piso="1", parede="0"),
        "salas": [
            {"x": s.x, "y": s.y, "largura": s.largura, "altura": s.altura} for s in grade.salas
        ],
        "inicio": inicio,
    }


def salvar_json(grade: Grade, algoritmo: str, semente: int, caminho: str | Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(para_dict(grade, algoritmo, semente)), encoding="utf-8")
    return caminho
