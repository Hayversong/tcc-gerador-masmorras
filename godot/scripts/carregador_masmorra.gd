extends Node2D
## Carrega uma masmorra exportada pelo gerador em Python (JSON) e a desenha
## em um TileMapLayer. Cada célula da grade vira um tile.
##
## Formato esperado do JSON (ver masmorras/exportacao.py):
##   "largura", "altura", "linhas" (strings com 0 = parede e 1 = piso),
##   "salas" (lista de {x, y, largura, altura}) e "inicio" ([x, y]).
##
## Teclas durante a execução: R recarrega o arquivo; Tab alterna entre
## os mapas de exemplo.

## Arquivo JSON a carregar.
@export_file("*.json") var caminho_mapa: String = "res://mapas/exemplo_bsp.json"
## Tamanho do tile em pixels (16 ou 32).
@export var tamanho_tile: int = 16
## TileSet próprio (opcional). Se vazio, é criado um TileSet simples com
## duas cores, o que permite testar sem arte.
@export var tileset_personalizado: TileSet
## Id da fonte do atlas e coordenadas dos tiles de parede e piso no TileSet.
@export var id_fonte: int = 0
@export var atlas_parede: Vector2i = Vector2i(0, 0)
@export var atlas_piso: Vector2i = Vector2i(1, 0)
## Ajusta a câmera para mostrar o mapa inteiro.
@export var enquadrar_camera: bool = true

const EXEMPLOS := ["res://mapas/exemplo_bsp.json", "res://mapas/exemplo_digger.json"]

@onready var camada: TileMapLayer = $TileMapLayer
@onready var camera: Camera2D = $Camera2D

var dados: Dictionary = {}


func _ready() -> void:
	camada.tile_set = tileset_personalizado if tileset_personalizado else criar_tileset_padrao(tamanho_tile)
	carregar(caminho_mapa)


func _unhandled_input(evento: InputEvent) -> void:
	if evento is InputEventKey and evento.pressed and not evento.echo:
		if evento.keycode == KEY_R:
			carregar(caminho_mapa)
		elif evento.keycode == KEY_TAB:
			var i := EXEMPLOS.find(caminho_mapa)
			caminho_mapa = EXEMPLOS[(i + 1) % EXEMPLOS.size()]
			carregar(caminho_mapa)


## Lê o JSON e desenha o mapa. Retorna false se o arquivo for inválido.
func carregar(caminho: String) -> bool:
	dados = ler_json(caminho)
	if dados.is_empty():
		return false
	desenhar(dados)
	if enquadrar_camera:
		_enquadrar()
	return true


static func ler_json(caminho: String) -> Dictionary:
	if not FileAccess.file_exists(caminho):
		push_error("Mapa não encontrado: %s" % caminho)
		return {}
	var conteudo: Variant = JSON.parse_string(FileAccess.get_file_as_string(caminho))
	if typeof(conteudo) != TYPE_DICTIONARY or not conteudo.has("linhas"):
		push_error("JSON de mapa inválido: %s" % caminho)
		return {}
	return conteudo


func desenhar(mapa: Dictionary) -> void:
	camada.clear()
	var linhas: Array = mapa["linhas"]
	for y in linhas.size():
		var linha: String = linhas[y]
		for x in linha.length():
			var atlas := atlas_piso if linha[x] == "1" else atlas_parede
			camada.set_cell(Vector2i(x, y), id_fonte, atlas)


## Posição (em pixels, no centro do tile) sugerida para o jogador começar.
func posicao_inicio() -> Vector2:
	if not dados.has("inicio"):
		return Vector2.ZERO
	var celula := Vector2i(int(dados["inicio"][0]), int(dados["inicio"][1]))
	return camada.map_to_local(celula)


func _enquadrar() -> void:
	var tamanho_mapa := Vector2(int(dados["largura"]), int(dados["altura"])) * tamanho_tile
	camera.position = tamanho_mapa / 2.0
	var tela := get_viewport_rect().size
	var escala := minf(tela.x / tamanho_mapa.x, tela.y / tamanho_mapa.y)
	camera.zoom = Vector2(escala, escala)


## TileSet de duas cores (parede escura, piso claro) gerado em código.
static func criar_tileset_padrao(t: int) -> TileSet:
	var imagem := Image.create(t * 2, t, false, Image.FORMAT_RGBA8)
	imagem.fill_rect(Rect2i(0, 0, t, t), Color("#2b2b33"))
	imagem.fill_rect(Rect2i(t, 0, t, t), Color("#b8a77c"))
	# piso com borda de 1 px, para a grade de tiles ficar visível
	imagem.fill_rect(Rect2i(t + 1, 1, t - 2, t - 2), Color("#c9b98f"))
	var fonte := TileSetAtlasSource.new()
	fonte.texture = ImageTexture.create_from_image(imagem)
	fonte.texture_region_size = Vector2i(t, t)
	fonte.create_tile(Vector2i(0, 0))
	fonte.create_tile(Vector2i(1, 0))
	var tileset := TileSet.new()
	tileset.tile_size = Vector2i(t, t)
	tileset.add_source(fonte, 0)
	return tileset
