"""Agente escavador "cego" estocástico (variante D1).

Baseado no pseudocódigo de Shaker et al. (2016, p. 39-40):

    Pc = 5 (chance de mudar de direção), Pr = 5 (chance de criar sala)
    posicionar o agente e sortear uma direção
    repetir:
        escavar na direção atual
        sortear Nc em [0, 100): se Nc < Pc, sortear nova direção e Pc = 0;
                                 senão Pc += 5
        sortear Nr em [0, 100): se Nr < Pr, criar sala 3..7 x 3..7 em volta
                                 do agente e Pr = 0; senão Pr += 5
    até a masmorra ficar "grande o suficiente"

Decisões de implementação:
- o agente parte do centro da grade;
- "grande o suficiente" = piso ocupando 35% das células da grade;
- teto de passos = 50 x número de células, para evitar laço infinito.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .grade import DIRECOES, Grade, Sala


@dataclass
class ParametrosDigger:
    cobertura_alvo: float = 0.35     # fração das células que deve virar piso
    chance_inicial: int = 5          # Pc e Pr iniciais (em %)
    incremento: int = 5              # aumento de Pc e Pr a cada passo sem o evento
    sala_min: int = 3                # lado mínimo da sala
    sala_max: int = 7                # lado máximo da sala
    fator_teto_passos: int = 50      # teto = fator x número de células


@dataclass
class ResultadoDigger:
    """Informações da execução, além da grade (usadas nas métricas)."""

    passos: int
    atingiu_cobertura: bool


def _direcoes_validas(grade: Grade, x: int, y: int):
    return [(dx, dy) for dx, dy in DIRECOES if grade.interior(x + dx, y + dy)]


def gerar_digger(
    largura: int, altura: int, semente: int, parametros: ParametrosDigger | None = None
) -> tuple[Grade, ResultadoDigger]:
    """Gera uma masmorra pelo agente escavador. Mesma semente produz o mesmo mapa."""
    p = parametros or ParametrosDigger()
    rng = random.Random(semente)
    grade = Grade(largura, altura)

    alvo = int(p.cobertura_alvo * grade.total_celulas())
    teto = p.fator_teto_passos * grade.total_celulas()

    x, y = largura // 2, altura // 2
    grade.escavar(x, y)
    direcao = rng.choice(DIRECOES)
    pc = pr = p.chance_inicial
    piso = grade.total_piso()
    passos = 0

    while piso < alvo and passos < teto:
        passos += 1

        # ao encontrar a borda, o agente sorteia outra direção válida
        if not grade.interior(x + direcao[0], y + direcao[1]):
            validas = _direcoes_validas(grade, x, y)
            if not validas:  # grade sem espaço para andar (ex.: 3 x 3)
                break
            direcao = rng.choice(validas)

        # escava um passo na direção atual
        x, y = x + direcao[0], y + direcao[1]
        piso += grade.escavar(x, y)

        # mudança de direção
        if rng.randrange(100) < pc:
            direcao = rng.choice(DIRECOES)
            pc = 0
        else:
            pc += p.incremento

        # criação de sala em volta da posição atual
        if rng.randrange(100) < pr:
            larg = rng.randint(p.sala_min, p.sala_max)
            alt = rng.randint(p.sala_min, p.sala_max)
            x0 = max(1, x - larg // 2)
            y0 = max(1, y - alt // 2)
            x1 = min(largura - 2, x0 + larg - 1)
            y1 = min(altura - 2, y0 + alt - 1)
            piso += grade.escavar_sala(Sala(x0, y0, x1 - x0 + 1, y1 - y0 + 1))
            pr = 0
        else:
            pr += p.incremento

    return grade, ResultadoDigger(passos=passos, atingiu_cobertura=piso >= alvo)
