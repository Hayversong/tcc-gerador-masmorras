"""Métricas de conectividade e de estrutura de uma masmorra em grade.

O tempo de geração é medido fora daqui (experimentos/executar.py), para que
o cálculo das métricas não entre na medição.
"""
from __future__ import annotations

from collections import deque
from statistics import mean, pstdev

from .grade import DIRECOES, PISO, Grade


def _rotular(grade: Grade, mascara: bytearray) -> tuple[list[int], int]:
    """Rotula componentes conexos (vizinhança 4) das células com mascara[i] == 1.

    Retorna (rotulos, quantidade); rótulo -1 indica célula fora da máscara.
    """
    L, A = grade.largura, grade.altura
    rotulos = [-1] * (L * A)
    n = 0
    for inicio in range(L * A):
        if not mascara[inicio] or rotulos[inicio] != -1:
            continue
        rotulos[inicio] = n
        fila = deque([inicio])
        while fila:
            i = fila.popleft()
            x, y = i % L, i // L
            for dx, dy in DIRECOES:
                nx, ny = x + dx, y + dy
                if 0 <= nx < L and 0 <= ny < A:
                    j = ny * L + nx
                    if mascara[j] and rotulos[j] == -1:
                        rotulos[j] = n
                        fila.append(j)
        n += 1
    return rotulos, n


def _distancias(grade: Grade, origem: int) -> list[int]:
    """Distância em passos (BFS, vizinhança 4) de `origem` até cada célula de piso."""
    L, A = grade.largura, grade.altura
    dist = [-1] * (L * A)
    dist[origem] = 0
    fila = deque([origem])
    cel = grade.celulas
    while fila:
        i = fila.popleft()
        x, y = i % L, i // L
        for dx, dy in DIRECOES:
            nx, ny = x + dx, y + dy
            if 0 <= nx < L and 0 <= ny < A:
                j = ny * L + nx
                if cel[j] == PISO and dist[j] == -1:
                    dist[j] = dist[i] + 1
                    fila.append(j)
    return dist


def _representantes(rot_regiao: list[int], n_regioes: int, L: int) -> list[int]:
    """Para cada região de sala, a célula da região mais próxima do seu centroide."""
    somas = [[0, 0, 0] for _ in range(n_regioes)]
    for i, r in enumerate(rot_regiao):
        if r != -1:
            somas[r][0] += i % L
            somas[r][1] += i // L
            somas[r][2] += 1
    centroides = [(sx / n, sy / n) for sx, sy, n in somas]
    melhor = [-1] * n_regioes
    melhor_d = [float("inf")] * n_regioes
    for i, r in enumerate(rot_regiao):
        if r != -1:
            cx, cy = centroides[r]
            d = (i % L - cx) ** 2 + (i // L - cy) ** 2
            if d < melhor_d[r]:
                melhor_d[r], melhor[r] = d, i
    return melhor


def _pontes_e_articulacoes(adjacencia: list[list[int]]) -> tuple[int, int]:
    """Conta pontes e pontos de articulação de um grafo não direcionado simples
    (algoritmo de Tarjan, versão iterativa)."""
    n = len(adjacencia)
    descoberta = [-1] * n
    menor = [0] * n
    tempo = 0
    pontes = 0
    articulacao = [False] * n
    for raiz in range(n):
        if descoberta[raiz] != -1:
            continue
        descoberta[raiz] = menor[raiz] = tempo
        tempo += 1
        filhos_raiz = 0
        pilha = [(raiz, -1, iter(adjacencia[raiz]))]
        while pilha:
            v, pai, vizinhos = pilha[-1]
            avancou = False
            for w in vizinhos:
                if descoberta[w] == -1:
                    descoberta[w] = menor[w] = tempo
                    tempo += 1
                    if v == raiz:
                        filhos_raiz += 1
                    pilha.append((w, v, iter(adjacencia[w])))
                    avancou = True
                    break
                if w != pai:
                    menor[v] = min(menor[v], descoberta[w])
            if avancou:
                continue
            pilha.pop()
            if pai != -1:
                menor[pai] = min(menor[pai], menor[v])
                if menor[v] > descoberta[pai]:
                    pontes += 1
                if pai != raiz and menor[v] >= descoberta[pai]:
                    articulacao[pai] = True
        if filhos_raiz > 1:
            articulacao[raiz] = True
    return pontes, sum(articulacao)


def calcular(grade: Grade) -> dict:
    L, A = grade.largura, grade.altura
    total = L * A
    piso_mask = bytearray(1 if c == PISO else 0 for c in grade.celulas)
    piso = sum(piso_mask)

    # ---------------- conectividade ----------------
    rot_piso, n_comp = _rotular(grade, piso_mask)

    salas = grade.salas
    if salas:
        cx, cy = salas[0].centro
        comp_ref = rot_piso[cy * L + cx]
        alcancaveis = sum(1 for s in salas if rot_piso[s.centro[1] * L + s.centro[0]] == comp_ref)
        fracao_alcancaveis = alcancaveis / len(salas)
    else:
        fracao_alcancaveis = 0.0

    # ---------------- estrutura ----------------
    sala_mask = bytearray(total)
    for s in salas:
        for x, y in s.celulas():
            sala_mask[y * L + x] = 1
    rot_regiao, n_regioes = _rotular(grade, sala_mask)

    corredor_mask = bytearray(1 if piso_mask[i] and not sala_mask[i] else 0 for i in range(total))
    corredor = sum(corredor_mask)
    rot_corr, n_corr = _rotular(grade, corredor_mask)

    areas = [s.area for s in salas]
    sobrepostas = sum(
        1 for i in range(len(salas)) for j in range(i + 1, len(salas)) if salas[i].sobrepoe(salas[j])
    )

    becos = 0
    for i in range(total):
        if piso_mask[i]:
            x, y = i % L, i // L
            if sum(1 for _ in grade.vizinhos_piso(x, y)) == 1:
                becos += 1

    # grafo bipartido: regiões de sala <-> componentes de corredor que se tocam
    arestas = set()
    for i in range(total):
        if corredor_mask[i]:
            x, y = i % L, i // L
            for dx, dy in DIRECOES:
                nx, ny = x + dx, y + dy
                if 0 <= nx < L and 0 <= ny < A:
                    r = rot_regiao[ny * L + nx]
                    if r != -1:
                        arestas.add((r, rot_corr[i]))
    vertices = n_regioes + n_corr
    # número ciclomático = E - V + C (C = componentes do grafo = componentes do piso)
    ciclos = len(arestas) - vertices + n_comp if vertices else 0

    # redundância das conexões: pontes e pontos de articulação do grafo
    # regiões de sala <-> componentes de corredor
    adjacencia = [[] for _ in range(vertices)]
    for r, c in arestas:
        adjacencia[r].append(n_regioes + c)
        adjacencia[n_regioes + c].append(r)
    pontes, articulacoes = _pontes_e_articulacoes(adjacencia)

    # distâncias entre regiões de sala (BFS a partir de cada região, exato)
    representantes = _representantes(rot_regiao, n_regioes, L)
    distancias = []
    for k, origem in enumerate(representantes):
        d = _distancias(grade, origem)
        for destino in representantes[k + 1:]:
            if d[destino] >= 0:
                distancias.append(d[destino])
    diametro = max(distancias) if distancias else 0
    distancia_media = round(mean(distancias), 2) if distancias else ""

    # ocupação espacial: caixa envolvente do piso / área interior
    xs = [i % L for i in range(total) if piso_mask[i]]
    ys = [i // L for i in range(total) if piso_mask[i]]
    caixa = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1) if xs else 0
    ocupacao = caixa / ((L - 2) * (A - 2))

    return {
        # conectividade
        "componentes_piso": n_comp,
        "totalmente_conectado": int(n_comp == 1),
        "fracao_salas_alcancaveis": round(fracao_alcancaveis, 4),
        # conectividade: redundância das conexões
        "ciclos": ciclos,
        "pontes": pontes,
        "fracao_pontes": round(pontes / len(arestas), 4) if arestas else 0.0,
        "pontos_articulacao": articulacoes,
        "fracao_articulacao": round(articulacoes / vertices, 4) if vertices else 0.0,
        "distancia_media_salas": distancia_media,
        # estrutura
        "salas_criadas": len(salas),
        "regioes_sala": n_regioes,
        "area_media_sala": round(mean(areas), 2) if areas else 0.0,
        "desvio_area_sala": round(pstdev(areas), 2) if areas else 0.0,
        "pares_salas_sobrepostas": sobrepostas,
        "cobertura_piso": round(piso / total, 4),
        "proporcao_corredor": round(corredor / piso, 4) if piso else 0.0,
        "becos_sem_saida": becos,
        "diametro_salas": diametro,
        "ocupacao_espacial": round(ocupacao, 4),
    }
