"""BSP clássico para geração de masmorras (variante B1).

Baseado na descrição de Shaker et al. (2016, p. 35-37):

1. a área da masmorra é a raiz da árvore BSP;
2. cada área é dividida por uma linha vertical ou horizontal enquanto for
   maior que o tamanho mínimo;
3. cada folha recebe uma sala com cantos sorteados dentro dos seus limites;
4. de baixo para cima, as salas dos filhos de um mesmo pai são ligadas por
   corredores, até ligar os dois filhos da raiz.

Decisões de implementação não especificadas na fonte: corte no lado maior
quando a área é muito alongada, posição do corte entre 30% e 70% do lado,
e, quando um filho é nó interno, sorteio de uma das salas da subárvore.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .grade import Grade, Sala


@dataclass
class ParametrosBSP:
    folha_minima: int = 8          # menor lado permitido para uma folha
    proporcao_min: float = 0.3     # posição mínima do corte (fração do lado)
    proporcao_max: float = 0.7     # posição máxima do corte
    sala_minima: int = 3           # menor lado de uma sala
    margem: int = 1                # células de parede entre sala e limite da folha


@dataclass
class No:
    x: int
    y: int
    largura: int
    altura: int
    esquerda: "No | None" = None
    direita: "No | None" = None
    sala: Sala | None = None

    @property
    def folha(self) -> bool:
        return self.esquerda is None


def _pode_dividir(tamanho: int, p: ParametrosBSP) -> bool:
    # cada parte precisa ter pelo menos folha_minima
    return tamanho >= 2 * p.folha_minima


def _posicao_corte(tamanho: int, rng: random.Random, p: ParametrosBSP) -> int:
    """Sorteia onde cortar um lado de `tamanho`, respeitando proporção e folha mínima."""
    menor = max(p.folha_minima, int(tamanho * p.proporcao_min))
    maior = min(tamanho - p.folha_minima, int(tamanho * p.proporcao_max))
    if menor > maior:  # lado pequeno: corta no meio
        return tamanho // 2
    return rng.randint(menor, maior)


def _dividir(no: No, rng: random.Random, p: ParametrosBSP) -> None:
    pode_v = _pode_dividir(no.largura, p)
    pode_h = _pode_dividir(no.altura, p)
    if not (pode_v or pode_h):
        return

    if pode_v and pode_h:
        # orientação sorteada, como na fonte; áreas muito alongadas são
        # cortadas no lado maior para evitar salas em "fita"
        if no.largura >= 1.25 * no.altura:
            vertical = True
        elif no.altura >= 1.25 * no.largura:
            vertical = False
        else:
            vertical = rng.random() < 0.5
    else:
        vertical = pode_v

    if vertical:
        c = _posicao_corte(no.largura, rng, p)
        no.esquerda = No(no.x, no.y, c, no.altura)
        no.direita = No(no.x + c, no.y, no.largura - c, no.altura)
    else:
        c = _posicao_corte(no.altura, rng, p)
        no.esquerda = No(no.x, no.y, no.largura, c)
        no.direita = No(no.x, no.y + c, no.largura, no.altura - c)

    _dividir(no.esquerda, rng, p)
    _dividir(no.direita, rng, p)


def _criar_sala(no: No, rng: random.Random, p: ParametrosBSP) -> Sala:
    """Sorteia dois cantos dentro da folha (respeitando a margem e o tamanho mínimo)."""
    x_min, y_min = no.x + p.margem, no.y + p.margem
    x_max, y_max = no.x + no.largura - 1 - p.margem, no.y + no.altura - 1 - p.margem
    larg = rng.randint(p.sala_minima, x_max - x_min + 1)
    alt = rng.randint(p.sala_minima, y_max - y_min + 1)
    x = rng.randint(x_min, x_max - larg + 1)
    y = rng.randint(y_min, y_max - alt + 1)
    return Sala(x, y, larg, alt)


def _salas_da_subarvore(no: No) -> list[Sala]:
    if no.folha:
        return [no.sala]
    return _salas_da_subarvore(no.esquerda) + _salas_da_subarvore(no.direita)


def _corredor_l(grade: Grade, a: tuple[int, int], b: tuple[int, int], rng: random.Random) -> None:
    """Escava um corredor em "L" entre os pontos a e b."""
    (x1, y1), (x2, y2) = a, b
    if rng.random() < 0.5:  # horizontal depois vertical
        cantos = [(x1, y1), (x2, y1), (x2, y2)]
    else:                   # vertical depois horizontal
        cantos = [(x1, y1), (x1, y2), (x2, y2)]
    for (ax, ay), (bx, by) in zip(cantos, cantos[1:]):
        for x in range(min(ax, bx), max(ax, bx) + 1):
            for y in range(min(ay, by), max(ay, by) + 1):
                grade.escavar(x, y)


def _ligar(no: No, grade: Grade, rng: random.Random) -> None:
    """Liga recursivamente, de baixo para cima, as salas dos filhos de cada nó."""
    if no.folha:
        return
    _ligar(no.esquerda, grade, rng)
    _ligar(no.direita, grade, rng)
    sala_a = rng.choice(_salas_da_subarvore(no.esquerda))
    sala_b = rng.choice(_salas_da_subarvore(no.direita))
    _corredor_l(grade, sala_a.centro, sala_b.centro, rng)


def gerar_bsp(largura: int, altura: int, semente: int, parametros: ParametrosBSP | None = None) -> Grade:
    """Gera uma masmorra pelo BSP clássico. Mesma semente produz o mesmo mapa."""
    p = parametros or ParametrosBSP()
    rng = random.Random(semente)
    grade = Grade(largura, altura)

    # a raiz é o interior da grade (a borda externa permanece parede)
    raiz = No(1, 1, largura - 2, altura - 2)
    _dividir(raiz, rng, p)

    pilha = [raiz]
    while pilha:
        no = pilha.pop()
        if no.folha:
            no.sala = _criar_sala(no, rng, p)
            grade.escavar_sala(no.sala)
        else:
            pilha.extend((no.direita, no.esquerda))

    _ligar(raiz, grade, rng)
    return grade
