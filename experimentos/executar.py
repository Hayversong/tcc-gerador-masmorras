"""Executa o experimento comparativo e grava uma linha de CSV por mapa gerado.

Desenho padrão: algoritmos {bsp, digger} x grades {40x30, 80x45, 160x90}
x sementes 0..999 (as mesmas para os dois algoritmos).

Exemplos:
    python -m experimentos.executar                       # experimento completo
    python -m experimentos.executar --sementes 10 --saida resultados/teste.csv
"""
import argparse
import csv
import json
import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

from masmorras.geradores import ALGORITMOS, gerar
from masmorras.metricas import calcular

GRADES_PADRAO = ((40, 30), (80, 45), (160, 90))


def _modelo_cpu() -> str:
    try:
        for linha in Path("/proc/cpuinfo").read_text().splitlines():
            if linha.startswith("model name"):
                return linha.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "desconhecido"


def descrever_ambiente(args) -> dict:
    """Dados da máquina e da execução, necessários para interpretar os tempos."""
    return {
        "data": datetime.now().isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "sistema": platform.platform(),
        "cpu": _modelo_cpu(),
        "nucleos_logicos": os.cpu_count(),
        "sementes": args.sementes,
        "aquecimento": args.aquecimento,
    }


def medir(algoritmo: str, largura: int, altura: int, semente: int):
    inicio = time.perf_counter_ns()
    grade, extra = gerar(algoritmo, largura, altura, semente)
    tempo_ns = time.perf_counter_ns() - inicio
    return grade, extra, tempo_ns


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sementes", type=int, default=1000, help="sementes 0..N-1 (padrão 1000)")
    ap.add_argument("--aquecimento", type=int, default=20,
                    help="execuções descartadas antes de medir cada combinação")
    ap.add_argument("--saida", default="resultados/metricas.csv")
    a = ap.parse_args()

    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    ambiente = descrever_ambiente(a)
    saida.with_name(saida.stem + "_ambiente.json").write_text(
        json.dumps(ambiente, indent=2, ensure_ascii=False), encoding="utf-8")
    print(" | ".join(f"{k}: {v}" for k, v in ambiente.items()), file=sys.stderr)

    with saida.open("w", newline="", encoding="utf-8") as f:
        escritor = None
        for largura, altura in GRADES_PADRAO:
            for algoritmo in ALGORITMOS:
                for s in range(a.aquecimento):  # aquecimento: não registrado
                    gerar(algoritmo, largura, altura, 10_000_000 + s)
                t0 = time.perf_counter()
                for semente in range(a.sementes):
                    grade, extra, tempo_ns = medir(algoritmo, largura, altura, semente)
                    linha = {
                        "algoritmo": algoritmo,
                        "largura": largura,
                        "altura": altura,
                        "semente": semente,
                        "tempo_ms": round(tempo_ns / 1e6, 4),
                        **extra,
                        **calcular(grade),
                    }
                    if escritor is None:
                        escritor = csv.DictWriter(f, fieldnames=list(linha))
                        escritor.writeheader()
                    escritor.writerow(linha)
                print(f"{algoritmo:>6} {largura}x{altura}: {a.sementes} mapas em "
                      f"{time.perf_counter() - t0:.1f} s", file=sys.stderr)
    print("resultados em", saida)


if __name__ == "__main__":
    main()
