"""Gera as figuras do TCC em figuras/ (PNG 300 dpi e PDF vetorial).

Ilustrações (não dependem do experimento):
  fig01_representacao_grade   grade 0/1 e o mapa correspondente
  fig02_bsp_particoes_arvore  partições do BSP e a árvore binária
  fig03_bsp_etapas            partições -> salas -> corredores
  fig04_digger_etapas         digger com 10%, 20% e 35% de piso
  fig05_exemplos_mapas        BSP e Digger nos três tamanhos de grade

Resultados (lêem resultados/metricas.csv):
  fig06_tempo                 tempo de geração por tamanho de grade
  fig07_conectividade         redundância das conexões
  fig08_estrutura             estrutura de salas e corredores

Uso (requer matplotlib; ver requirements-graficos.txt):
    python -m analise.graficos
"""
from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from masmorras.bsp import No, ParametrosBSP, _dividir, gerar_bsp  # noqa: E402
from masmorras.digger import ParametrosDigger, gerar_digger  # noqa: E402

PASTA = Path("figuras")
RESULTADOS = Path("resultados/metricas.csv")
GRADES = ((40, 30), (80, 45), (160, 90))
SEMENTE_EXEMPLO = 7

# cores: categóricas validadas (daltonismo e contraste) sobre fundo branco
COR = {"bsp": "#2a78d6", "digger": "#eb6834"}
NOME = {"bsp": "BSP", "digger": "Digger"}
PAREDE, PISO = "#2b2b33", "#ece6d6"
MAPA_CORES = ListedColormap([PAREDE, PISO])
TINTA, TINTA_2, GRADE_EIXO = "#1f1f1f", "#5c5c5c", "#d9d9d9"

plt.rcParams.update({
    "font.family": "Liberation Sans",
    "font.size": 9,
    "axes.edgecolor": GRADE_EIXO,
    "axes.labelcolor": TINTA,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "xtick.color": TINTA_2,
    "ytick.color": TINTA_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})


def virgula(fmt: str = "{:g}"):
    """Formatador de eixo com vírgula decimal (padrão brasileiro)."""
    return FuncFormatter(lambda v, _: fmt.format(v).replace(".", ","))


def salvar(fig, nome: str) -> None:
    PASTA.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(PASTA / f"{nome}.{ext}")
    plt.close(fig)
    print("  ", nome)


def matriz(grade) -> list[list[int]]:
    return [[grade.obter(x, y) for x in range(grade.largura)] for y in range(grade.altura)]


def desenhar_mapa(ax, grade, titulo: str | None = None) -> None:
    ax.imshow(matriz(grade), cmap=MAPA_CORES, vmin=0, vmax=1, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    for lado in ax.spines.values():
        lado.set_visible(False)
    if titulo:
        ax.set_title(titulo, loc="left")


def folhas(no: No) -> list[No]:
    return [no] if no.folha else folhas(no.esquerda) + folhas(no.direita)


def arvore_bsp(largura: int, altura: int, semente: int, p: ParametrosBSP | None = None) -> No:
    """Refaz a fase de partição de gerar_bsp com a mesma semente (mesma sequência
    aleatória), obtendo exatamente as partições usadas no mapa final."""
    p = p or ParametrosBSP()
    raiz = No(1, 1, largura - 2, altura - 2)
    _dividir(raiz, random.Random(semente), p)
    return raiz


def contorno_particoes(ax, raiz: No, cor: str = COR["bsp"]) -> None:
    for f in folhas(raiz):
        ax.add_patch(Rectangle((f.x - 0.5, f.y - 0.5), f.largura, f.altura,
                               fill=False, edgecolor=cor, linewidth=1.2))


# ------------------------------------------------------------------ ilustrações
def fig01_representacao_grade() -> None:
    p = ParametrosBSP(folha_minima=6)
    g = gerar_bsp(20, 12, 3, p)
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 2.3))
    a.imshow(matriz(g), cmap=ListedColormap(["#f4f4f4", PISO]), vmin=0, vmax=1)
    for y in range(g.altura):
        for x in range(g.largura):
            a.text(x, y, str(g.obter(x, y)), ha="center", va="center", fontsize=6,
                   color=TINTA if g.obter(x, y) else "#9a9a9a",
                   fontweight="bold" if g.obter(x, y) else "normal")
    a.set_xticks([])
    a.set_yticks([])
    a.set_title("(a) Matriz: 0 = parede, 1 = piso", loc="left")
    desenhar_mapa(b, g, "(b) Mapa correspondente (1 célula = 1 tile)")
    salvar(fig, "fig01_representacao_grade")


def _layout_arvore(no: No, prof: int, pos: dict, contador: list) -> float:
    if no.folha:
        x = contador[0]
        contador[0] += 1
    else:
        x = (_layout_arvore(no.esquerda, prof + 1, pos, contador)
             + _layout_arvore(no.direita, prof + 1, pos, contador)) / 2
    pos[id(no)] = (x, -prof)
    return x


def fig02_bsp_particoes_arvore() -> None:
    raiz = arvore_bsp(40, 30, SEMENTE_EXEMPLO)
    rotulos, letras = {}, iter("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def rotular(no):  # pré-ordem: A é a raiz, como em Shaker et al. (2016)
        rotulos[id(no)] = next(letras)
        if not no.folha:
            rotular(no.esquerda)
            rotular(no.direita)
    rotular(raiz)

    fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 2.8), gridspec_kw={"width_ratios": [1, 1.15]})
    a.imshow([[0] * 40 for _ in range(30)], cmap=ListedColormap([PISO]))
    contorno_particoes(a, raiz)
    for f in folhas(raiz):
        a.text(f.x + f.largura / 2 - 0.5, f.y + f.altura / 2 - 0.5, rotulos[id(f)],
               ha="center", va="center", fontsize=8, color=TINTA)
    a.set_xticks([])
    a.set_yticks([])
    a.set_title("(a) Partições (folhas da árvore)", loc="left")

    pos = {}
    _layout_arvore(raiz, 0, pos, [0])

    def ligar(no):
        if no.folha:
            return
        for filho in (no.esquerda, no.direita):
            (x1, y1), (x2, y2) = pos[id(no)], pos[id(filho)]
            b.plot([x1, x2], [y1, y2], color=GRADE_EIXO, linewidth=1.2, zorder=1)
            ligar(filho)
    ligar(raiz)

    def nos(no):
        yield no
        if not no.folha:
            yield from nos(no.esquerda)
            yield from nos(no.direita)
    for no in nos(raiz):
        x, y = pos[id(no)]
        b.scatter([x], [y], s=150, zorder=2, color=COR["bsp"] if no.folha else "white",
                  edgecolors=COR["bsp"], linewidths=1.2)
        b.text(x, y, rotulos[id(no)], ha="center", va="center", fontsize=7, zorder=3,
               color="white" if no.folha else TINTA)
    b.axis("off")
    b.set_title("(b) Árvore BSP (folhas preenchidas)", loc="left")
    salvar(fig, "fig02_bsp_particoes_arvore")


def fig03_bsp_etapas() -> None:
    largura, altura = 80, 45
    raiz = arvore_bsp(largura, altura, SEMENTE_EXEMPLO)
    final = gerar_bsp(largura, altura, SEMENTE_EXEMPLO)

    fig, eixos = plt.subplots(1, 3, figsize=(6.3, 1.45))
    vazio = [[0] * largura for _ in range(altura)]
    eixos[0].imshow(vazio, cmap=MAPA_CORES, vmin=0, vmax=1)
    contorno_particoes(eixos[0], raiz, cor="#86b6ef")
    so_salas = [[0] * largura for _ in range(altura)]
    for s in final.salas:
        for x, y in s.celulas():
            so_salas[y][x] = 1
    eixos[1].imshow(so_salas, cmap=MAPA_CORES, vmin=0, vmax=1)
    contorno_particoes(eixos[1], raiz, cor="#86b6ef")
    eixos[2].imshow(matriz(final), cmap=MAPA_CORES, vmin=0, vmax=1)
    for ax, t in zip(eixos, ("(a) Partição recursiva", "(b) Uma sala por folha", "(c) Corredores entre irmãos")):
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(t, loc="left", fontsize=8.5)
        for lado in ax.spines.values():
            lado.set_visible(False)
    salvar(fig, "fig03_bsp_etapas")


def fig04_digger_etapas() -> None:
    largura, altura = 80, 45
    fig, eixos = plt.subplots(1, 3, figsize=(6.3, 1.45))
    for ax, alvo, rot in zip(eixos, (0.10, 0.20, 0.35), "abc"):
        # mesma semente: cada execução é um prefixo exato da execução com 35%
        g, r = gerar_digger(largura, altura, SEMENTE_EXEMPLO, ParametrosDigger(cobertura_alvo=alvo))
        desenhar_mapa(ax, g, f"({rot}) {int(alvo * 100)}% de piso\n{r.passos} passos do agente")
        ax.title.set_fontsize(8.5)
        ax.scatter([largura // 2], [altura // 2], s=14, color=COR["digger"], edgecolors="white",
                   linewidths=0.8, zorder=3)
    eixos[0].legend(handles=[Patch(color=COR["digger"], label="início do agente (centro)")],
                    loc="lower left", fontsize=7, frameon=False, bbox_to_anchor=(0, -0.32))
    salvar(fig, "fig04_digger_etapas")


def fig05_exemplos_mapas() -> None:
    fig, eixos = plt.subplots(3, 2, figsize=(6.3, 6.2),
                              gridspec_kw={"height_ratios": [h / w for w, h in GRADES]})
    for i, (largura, altura) in enumerate(GRADES):
        desenhar_mapa(eixos[i][0], gerar_bsp(largura, altura, SEMENTE_EXEMPLO), f"BSP, {largura}×{altura}")
        desenhar_mapa(eixos[i][1], gerar_digger(largura, altura, SEMENTE_EXEMPLO)[0],
                      f"Digger, {largura}×{altura}")
    for ax in eixos.flat:
        ax.title.set_fontsize(8.5)
    fig.tight_layout(h_pad=1.2)
    salvar(fig, "fig05_exemplos_mapas")


# ------------------------------------------------------------------ resultados
def carregar_resultados() -> dict:
    dados = defaultdict(list)  # (algoritmo, (l, a), métrica) -> valores
    with RESULTADOS.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            chave = (int(linha["largura"]), int(linha["altura"]))
            for m, v in linha.items():
                if m not in ("algoritmo", "largura", "altura") and v != "":
                    dados[(linha["algoritmo"], chave, m)].append(float(v))
    return dados


def boxplots(ax, dados, metrica: str, titulo: str, rotulo_y: str, log: bool = False) -> None:
    largura_caixa, deslocamento = 0.32, 0.19
    for k, alg in enumerate(("bsp", "digger")):
        series = [dados[(alg, g, metrica)] for g in GRADES]
        posicoes = [i + (deslocamento if k else -deslocamento) for i in range(len(GRADES))]
        bp = ax.boxplot(series, positions=posicoes, widths=largura_caixa, patch_artist=True,
                        showfliers=False, medianprops={"color": "white", "linewidth": 1.5},
                        whiskerprops={"color": COR[alg], "linewidth": 1},
                        capprops={"color": COR[alg], "linewidth": 1})
        for caixa in bp["boxes"]:
            caixa.set(facecolor=COR[alg], edgecolor=COR[alg])
        # ponto na mediana: mantém visível uma caixa de altura quase zero
        medianas = [sorted(v)[len(v) // 2] for v in series]
        ax.scatter(posicoes, medianas, s=16, color=COR[alg], edgecolors="white",
                   linewidths=0.8, zorder=4)
    ax.set_xticks(range(len(GRADES)), [f"{w}×{h}" for w, h in GRADES])
    ax.set_title(titulo, loc="left")
    ax.set_ylabel(rotulo_y)
    if log:
        ax.set_yscale("log")
    ax.yaxis.set_major_formatter(virgula())
    ax.grid(axis="y", color=GRADE_EIXO, linewidth=0.6)
    ax.set_axisbelow(True)


def legenda_algoritmos(fig) -> None:
    fig.legend(handles=[Patch(color=COR[a], label=NOME[a]) for a in ("bsp", "digger")],
               loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.04))


def fig06_tempo(dados) -> None:
    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    celulas = [w * h for w, h in GRADES]
    for alg in ("bsp", "digger"):
        medianas, q1s, q3s = [], [], []
        for g in GRADES:
            v = sorted(dados[(alg, g, "tempo_ms")])
            medianas.append(v[len(v) // 2])
            q1s.append(v[len(v) // 4])
            q3s.append(v[3 * len(v) // 4])
        ax.plot(celulas, medianas, color=COR[alg], linewidth=2, marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=1, label=NOME[alg])
        ax.fill_between(celulas, q1s, q3s, color=COR[alg], alpha=0.18, linewidth=0)
        ax.annotate(NOME[alg], (celulas[-1], medianas[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8, color=TINTA)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(celulas, [f"{w}×{h}\n({w * h:,} células)".replace(",", ".") for w, h in GRADES])
    ax.minorticks_off()
    ax.set_yticks([0.1, 0.2, 0.5, 1, 2, 5, 10])
    ax.set_ylim(0.1, 10)
    ax.yaxis.set_major_formatter(virgula())
    ax.set_ylabel("Tempo de geração (ms, escala log)")
    ax.grid(color=GRADE_EIXO, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left")
    salvar(fig, "fig06_tempo")


def fig07_conectividade(dados) -> None:
    fig, eixos = plt.subplots(2, 2, figsize=(6.3, 4.4))
    boxplots(eixos[0][0], dados, "ciclos", "(a) Ciclos (caminhos alternativos)", "Quantidade")
    boxplots(eixos[0][1], dados, "fracao_pontes", "(b) Fração de ligações críticas (pontes)", "Fração")
    boxplots(eixos[1][0], dados, "fracao_articulacao", "(c) Fração de pontos de articulação", "Fração")
    boxplots(eixos[1][1], dados, "distancia_media_salas", "(d) Distância média entre salas", "Passos")
    legenda_algoritmos(fig)
    fig.tight_layout()
    salvar(fig, "fig07_conectividade")


def fig08_estrutura(dados) -> None:
    fig, eixos = plt.subplots(2, 3, figsize=(6.3, 4.2))
    boxplots(eixos[0][0], dados, "regioes_sala", "(a) Regiões de sala", "Quantidade", log=True)
    boxplots(eixos[0][1], dados, "area_media_sala", "(b) Área média da sala", "Células")
    boxplots(eixos[0][2], dados, "proporcao_corredor", "(c) Proporção de corredor", "Fração do piso")
    boxplots(eixos[1][0], dados, "becos_sem_saida", "(d) Becos sem saída", "Células")
    boxplots(eixos[1][1], dados, "ocupacao_espacial", "(e) Ocupação espacial", "Fração da área")
    boxplots(eixos[1][2], dados, "diametro_salas", "(f) Maior distância entre salas", "Passos")
    for ax in eixos.flat:
        ax.title.set_fontsize(8.5)
        ax.tick_params(axis="x", labelsize=7)
    legenda_algoritmos(fig)
    fig.tight_layout()
    salvar(fig, "fig08_estrutura")


def main() -> None:
    print("ilustrações:")
    fig01_representacao_grade()
    fig02_bsp_particoes_arvore()
    fig03_bsp_etapas()
    fig04_digger_etapas()
    fig05_exemplos_mapas()
    if RESULTADOS.exists():
        print("resultados:")
        dados = carregar_resultados()
        fig06_tempo(dados)
        fig07_conectividade(dados)
        fig08_estrutura(dados)
    else:
        print("resultados/metricas.csv não encontrado: gráficos de resultados ignorados")


if __name__ == "__main__":
    main()
