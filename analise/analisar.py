"""Análise estatística dos resultados do experimento.

Lê resultados/metricas.csv e, para cada tamanho de grade e cada métrica,
compara BSP e Digger com:
  - média, desvio-padrão, mediana, p95, mínimo e máximo por algoritmo;
  - teste de Mann-Whitney U bilateral (aproximação normal com correção de
    empates e de continuidade);
  - tamanho de efeito: correlação rank-biserial r = 2U/(n1 n2) - 1, em que U
    é o U do BSP (r > 0 indica valores maiores no BSP).

Gera resultados/resumo.csv e resultados/resumo.md.

Uso:
    python -m analise.analisar [--entrada resultados/metricas.csv] [--alfa 0.05]
"""
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev

METRICAS = (
    # (coluna, dimensão)
    ("tempo_ms", "tempo"),
    ("totalmente_conectado", "conectividade"),
    ("componentes_piso", "conectividade"),
    ("fracao_salas_alcancaveis", "conectividade"),
    ("ciclos", "conectividade"),
    ("pontes", "conectividade"),
    ("fracao_pontes", "conectividade"),
    ("pontos_articulacao", "conectividade"),
    ("fracao_articulacao", "conectividade"),
    ("distancia_media_salas", "conectividade"),
    ("salas_criadas", "estrutura"),
    ("regioes_sala", "estrutura"),
    ("area_media_sala", "estrutura"),
    ("pares_salas_sobrepostas", "estrutura"),
    ("cobertura_piso", "estrutura"),
    ("proporcao_corredor", "estrutura"),
    ("becos_sem_saida", "estrutura"),
    ("diametro_salas", "estrutura"),
    ("ocupacao_espacial", "estrutura"),
)


def percentil(valores: list[float], q: float) -> float:
    """Percentil por interpolação linear (mesmo método padrão do NumPy)."""
    v = sorted(valores)
    pos = (len(v) - 1) * q
    i = math.floor(pos)
    j = min(i + 1, len(v) - 1)
    return v[i] + (v[j] - v[i]) * (pos - i)


def mann_whitney(a: list[float], b: list[float]) -> tuple[float, float]:
    """Retorna (U de `a`, p bilateral)."""
    n1, n2 = len(a), len(b)
    n = n1 + n2
    combinados = sorted([(x, 0) for x in a] + [(x, 1) for x in b])
    postos = [0.0] * n
    correcao_empates = 0.0
    i = 0
    while i < n:
        j = i
        while j + 1 < n and combinados[j + 1][0] == combinados[i][0]:
            j += 1
        posto_medio = (i + j) / 2 + 1
        for k in range(i, j + 1):
            postos[k] = posto_medio
        t = j - i + 1
        correcao_empates += t ** 3 - t
        i = j + 1
    r1 = sum(p for p, (_, g) in zip(postos, combinados) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sigma2 = n1 * n2 / 12 * ((n + 1) - correcao_empates / (n * (n - 1)))
    if sigma2 <= 0:
        return u1, 1.0
    z = (abs(u1 - mu) - 0.5) / math.sqrt(sigma2)
    z = max(z, 0.0)
    return u1, math.erfc(z / math.sqrt(2))


def descrever(v: list[float]) -> dict:
    return {
        "media": mean(v),
        "desvio": pstdev(v),
        "mediana": median(v),
        "p95": percentil(v, 0.95),
        "min": min(v),
        "max": max(v),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default="resultados/metricas.csv")
    ap.add_argument("--alfa", type=float, default=0.05)
    a = ap.parse_args()

    entrada = Path(a.entrada)
    dados = defaultdict(lambda: defaultdict(list))  # (grade) -> (algoritmo, metrica) -> valores
    with entrada.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            grade = f"{linha['largura']}x{linha['altura']}"
            for m, _ in METRICAS:
                if linha[m] != "":  # vazio = métrica indefinida (ex.: só uma região de sala)
                    dados[grade][(linha["algoritmo"], m)].append(float(linha[m]))

    linhas = []
    for grade in sorted(dados, key=lambda g: int(g.split("x")[0])):
        for m, dim in METRICAS:
            bsp = dados[grade][("bsp", m)]
            dig = dados[grade][("digger", m)]
            u, p = mann_whitney(bsp, dig)
            r = 2 * u / (len(bsp) * len(dig)) - 1
            db, dd = descrever(bsp), descrever(dig)
            linhas.append({
                "grade": grade, "dimensao": dim, "metrica": m, "n_bsp": len(bsp), "n_digger": len(dig),
                **{f"bsp_{k}": v for k, v in db.items()},
                **{f"digger_{k}": v for k, v in dd.items()},
                "U_bsp": u, "p_valor": p, "rank_biserial": r, "significativo": int(p < a.alfa),
            })

    saida_csv = entrada.with_name("resumo.csv")
    with saida_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        for l in linhas:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in l.items()})

    md = [f"# Resumo do experimento\n",
          f"Fonte: `{entrada}` · teste de Mann-Whitney U bilateral, α = {a.alfa} · "
          "r = correlação rank-biserial (r > 0: valores maiores no BSP).\n"]
    for grade in dict.fromkeys(l["grade"] for l in linhas):
        md.append(f"\n## Grade {grade}\n")
        md.append("| Dimensão | Métrica | n (BSP/Digger) | BSP média (DP) | BSP mediana | Digger média (DP) | Digger mediana | p | r |")
        md.append("|---|---|---|---|---|---|---|---|---|")
        for l in (x for x in linhas if x["grade"] == grade):
            p = "< 0,001" if l["p_valor"] < 0.001 else f"{l['p_valor']:.3f}".replace(".", ",")
            fmt = lambda v: f"{v:.3f}".replace(".", ",")
            md.append(
                f"| {l['dimensao']} | {l['metrica']} | {l['n_bsp']}/{l['n_digger']} | {fmt(l['bsp_media'])} ({fmt(l['bsp_desvio'])}) | "
                f"{fmt(l['bsp_mediana'])} | {fmt(l['digger_media'])} ({fmt(l['digger_desvio'])}) | "
                f"{fmt(l['digger_mediana'])} | {p} | {fmt(l['rank_biserial'])} |"
            )
    saida_md = entrada.with_name("resumo.md")
    saida_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("gerados:", saida_csv, saida_md)


if __name__ == "__main__":
    main()
