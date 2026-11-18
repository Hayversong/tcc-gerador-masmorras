"""Gera uma masmorra e salva em JSON. Ponto de entrada usado pela Godot.

Pode ser chamado de qualquer pasta, porque o diretório deste arquivo entra
no caminho de importação do Python:
    python3 /caminho/gerador-masmorras/gerar_mapa.py --algoritmo bsp --largura 80 --altura 45 --semente 7 --saida mapa.json
"""
from experimentos.exportar import main

if __name__ == "__main__":
    main()
