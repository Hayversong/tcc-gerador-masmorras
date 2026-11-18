"""Representação de uma masmorra 2D em grade.

Cada célula é PAREDE (0) ou PISO (1). A borda externa da grade é sempre
parede, de modo que nenhum algoritmo escava até a borda.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PAREDE = 0
PISO = 1

# vizinhança de von Neumann (4 direções): cima, baixo, esquerda, direita
DIRECOES = ((0, -1), (0, 1), (-1, 0), (1, 0))


@dataclass(frozen=True)
class Sala:
    """Retângulo de uma sala; (x, y) é o canto superior esquerdo."""

    x: int
    y: int
    largura: int
    altura: int

    @property
    def x2(self) -> int:
        """Última coluna da sala (inclusiva)."""
        return self.x + self.largura - 1

    @property
    def y2(self) -> int:
        """Última linha da sala (inclusiva)."""
        return self.y + self.altura - 1

    @property
    def area(self) -> int:
        return self.largura * self.altura

    @property
    def centro(self) -> tuple[int, int]:
        return (self.x + self.largura // 2, self.y + self.altura // 2)

    def contem(self, x: int, y: int) -> bool:
        return self.x <= x <= self.x2 and self.y <= y <= self.y2

    def sobrepoe(self, outra: "Sala") -> bool:
        return not (
            self.x2 < outra.x or outra.x2 < self.x or self.y2 < outra.y or outra.y2 < self.y
        )

    def celulas(self):
        for y in range(self.y, self.y2 + 1):
            for x in range(self.x, self.x2 + 1):
                yield x, y


@dataclass
class Grade:
    """Grade de largura × altura células, inicialmente toda parede."""

    largura: int
    altura: int
    celulas: bytearray = field(init=False)
    salas: list[Sala] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.largura < 3 or self.altura < 3:
            raise ValueError("a grade precisa ter pelo menos 3 x 3 células")
        self.celulas = bytearray(self.largura * self.altura)  # tudo PAREDE

    # ---- acesso ----
    def _indice(self, x: int, y: int) -> int:
        return y * self.largura + x

    def dentro(self, x: int, y: int) -> bool:
        """Verdadeiro se (x, y) está na grade, incluindo a borda."""
        return 0 <= x < self.largura and 0 <= y < self.altura

    def interior(self, x: int, y: int) -> bool:
        """Verdadeiro se (x, y) está na grade e fora da borda externa."""
        return 1 <= x < self.largura - 1 and 1 <= y < self.altura - 1

    def obter(self, x: int, y: int) -> int:
        return self.celulas[self._indice(x, y)]

    def eh_piso(self, x: int, y: int) -> bool:
        return self.dentro(x, y) and self.celulas[self._indice(x, y)] == PISO

    # ---- escavação ----
    def escavar(self, x: int, y: int) -> bool:
        """Transforma (x, y) em piso. Retorna True se a célula era parede.

        Células da borda externa nunca são escavadas.
        """
        if not self.interior(x, y):
            return False
        i = self._indice(x, y)
        if self.celulas[i] == PISO:
            return False
        self.celulas[i] = PISO
        return True

    def escavar_sala(self, sala: Sala) -> int:
        """Escava o retângulo da sala e a registra. Retorna quantas células mudaram."""
        novas = sum(self.escavar(x, y) for x, y in sala.celulas())
        self.salas.append(sala)
        return novas

    # ---- consultas ----
    def total_piso(self) -> int:
        return self.celulas.count(PISO)

    def total_celulas(self) -> int:
        return self.largura * self.altura

    def vizinhos_piso(self, x: int, y: int):
        for dx, dy in DIRECOES:
            nx, ny = x + dx, y + dy
            if self.eh_piso(nx, ny):
                yield nx, ny

    def linhas(self, piso: str = ".", parede: str = "#") -> list[str]:
        """Representação textual, uma string por linha."""
        mapa = {PISO: piso, PAREDE: parede}
        return [
            "".join(mapa[self.celulas[y * self.largura + x]] for x in range(self.largura))
            for y in range(self.altura)
        ]

    def __str__(self) -> str:
        return "\n".join(self.linhas())
