extends Node2D
## Cena principal: carrega uma masmorra em JSON (gerada pelo Python), desenha
## no TileMapLayer e permite explorá-la com um personagem.
##
## Formato esperado do JSON (masmorras/exportacao.py):
##   "largura", "altura", "linhas" (strings com 0 = parede e 1 = piso),
##   "salas" (lista de {x, y, largura, altura}), "inicio" ([x, y]),
##   "algoritmo" e "semente".
##
## Controles: setas ou WASD movem o personagem uma célula; G gera outra
## masmorra com semente aleatória; M alterna entre seguir o personagem e ver
## o mapa inteiro; roda do mouse aproxima e afasta; R recarrega; Tab alterna
## entre os mapas de exemplo. Chegar à escada gera o próximo nível.

const MarcadorScript := preload("res://scripts/marcador.gd")

## Arquivo JSON carregado ao iniciar.
@export_file("*.json") var caminho_mapa: String = "res://mapas/exemplo_bsp.json"
## Tamanho do tile em pixels (16 ou 32).
@export var tamanho_tile: int = 16
## TileSet próprio (opcional). Se vazio, é criado um TileSet de duas cores.
@export var tileset_personalizado: TileSet
## Id da fonte do atlas e coordenadas dos tiles de parede e piso no TileSet.
@export var id_fonte: int = 0
@export var atlas_parede: Vector2i = Vector2i(0, 0)
@export var atlas_piso: Vector2i = Vector2i(1, 0)
## Começa mostrando o mapa inteiro (em vez de seguir o personagem).
@export var enquadrar_camera: bool = true
## Cria o painel de geração e o personagem. Desligado nos testes e capturas.
@export var modo_interativo: bool = true
## Executável do Python usado para gerar mapas ("python" no Windows).
@export var comando_python: String = "python3"
## Pasta do gerador em Python. Vazio = pasta acima do projeto Godot.
@export_global_dir var pasta_gerador: String = ""
## Aproximação da câmera quando segue o personagem.
@export_range(0.5, 8.0, 0.25) var zoom_seguindo: float = 3.0

const EXEMPLOS := ["res://mapas/exemplo_bsp.json", "res://mapas/exemplo_digger.json"]
const ALGORITMOS := ["bsp", "digger"]
const NOMES_ALGORITMOS := ["BSP", "Digger"]
const TAMANHOS := [Vector2i(40, 30), Vector2i(80, 45), Vector2i(160, 90)]
const LARGURA_PAINEL := 320.0

@onready var camada: TileMapLayer = $TileMapLayer
@onready var camera: Camera2D = $Camera2D

var dados: Dictionary = {}
var nivel: int = 1
var jogador: Node2D
var escada: Node2D

var _opcao_algoritmo: OptionButton
var _opcao_tamanho: OptionButton
var _campo_semente: SpinBox
var _rotulo_info: Label
var _rotulo_status: Label


func _ready() -> void:
	camada.tile_set = tileset_personalizado if tileset_personalizado else criar_tileset_padrao(tamanho_tile)
	escada = _criar_marcador(MarcadorScript.Tipo.ESCADA)
	jogador = _criar_marcador(MarcadorScript.Tipo.JOGADOR)
	if modo_interativo:
		_criar_interface()
	else:
		jogador.visible = false
		escada.visible = false
	carregar(caminho_mapa)


# ------------------------------------------------------------------ mapa

## Lê o JSON e desenha o mapa. Retorna false se o arquivo for inválido.
func carregar(caminho: String) -> bool:
	var novo := ler_json(caminho)
	if novo.is_empty():
		_status("Não foi possível ler %s" % caminho)
		return false
	dados = novo
	caminho_mapa = caminho
	desenhar(dados)
	_posicionar_marcadores()
	_atualizar_camera()
	_atualizar_info()
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


## Verdadeiro se a célula existe no mapa e é piso.
func eh_piso(celula: Vector2i) -> bool:
	if dados.is_empty():
		return false
	var linhas: Array = dados["linhas"]
	if celula.y < 0 or celula.y >= linhas.size():
		return false
	var linha: String = linhas[celula.y]
	return celula.x >= 0 and celula.x < linha.length() and linha[celula.x] == "1"


## Célula inicial sugerida pelo JSON.
func celula_inicio() -> Vector2i:
	if dados.has("inicio"):
		return Vector2i(int(dados["inicio"][0]), int(dados["inicio"][1]))
	return Vector2i.ZERO


## Posição (em pixels, no centro do tile) sugerida para o jogador começar.
func posicao_inicio() -> Vector2:
	return camada.map_to_local(celula_inicio())


## Célula de piso mais distante da origem, em passos (busca em largura).
func celula_mais_distante(origem: Vector2i) -> Vector2i:
	var distancia := {origem: 0}
	var fila: Array[Vector2i] = [origem]
	var mais_longe := origem
	var i := 0
	while i < fila.size():
		var atual: Vector2i = fila[i]
		i += 1
		for passo in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
			var viz: Vector2i = atual + passo
			if eh_piso(viz) and not distancia.has(viz):
				distancia[viz] = distancia[atual] + 1
				fila.append(viz)
				if distancia[viz] > distancia[mais_longe]:
					mais_longe = viz
	return mais_longe


# ------------------------------------------------------------------ jogo

## Move o jogador uma célula. Retorna true se andou (não atravessa paredes).
func mover(passo: Vector2i) -> bool:
	var alvo := (jogador.get("celula") as Vector2i) + passo
	if not eh_piso(alvo):
		return false
	_colocar(jogador, alvo)
	if not enquadrar_camera:
		camera.position = jogador.position
	if alvo == escada.get("celula") and modo_interativo:
		_proximo_nivel()
	return true


func _proximo_nivel() -> void:
	nivel += 1
	_campo_semente.value = randi() % 1000000
	if not gerar_atual():
		nivel -= 1


## Gera uma masmorra chamando o gerador em Python e a carrega.
func gerar(algoritmo: String, tamanho: Vector2i, semente: int) -> bool:
	var raiz := pasta_gerador
	if raiz.is_empty():
		raiz = ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	var script_py := raiz.path_join("gerar_mapa.py")
	var saida_json := OS.get_user_data_dir().path_join("mapa_gerado.json")
	var args := [script_py, "--algoritmo", algoritmo, "--largura", str(tamanho.x),
		"--altura", str(tamanho.y), "--semente", str(semente), "--saida", saida_json]
	var saida := []
	var codigo := OS.execute(comando_python, args, saida, true)
	if codigo != 0:
		_status("Falha ao gerar (código %d). Confira 'comando_python' e 'pasta_gerador'.\n%s" % [codigo, "".join(saida)])
		return false
	return carregar(saida_json)


## Gera com as opções escolhidas no painel.
func gerar_atual() -> bool:
	return gerar(ALGORITMOS[_opcao_algoritmo.selected], TAMANHOS[_opcao_tamanho.selected], int(_campo_semente.value))


func _unhandled_input(evento: InputEvent) -> void:
	if evento is InputEventKey and evento.pressed:
		var passo := Vector2i.ZERO
		match evento.keycode:
			KEY_UP, KEY_W: passo = Vector2i.UP
			KEY_DOWN, KEY_S: passo = Vector2i.DOWN
			KEY_LEFT, KEY_A: passo = Vector2i.LEFT
			KEY_RIGHT, KEY_D: passo = Vector2i.RIGHT
		if passo != Vector2i.ZERO:
			mover(passo)
			get_viewport().set_input_as_handled()
			return
		if evento.echo:
			return
		match evento.keycode:
			KEY_G:
				if modo_interativo:
					_campo_semente.value = randi() % 1000000
					gerar_atual()
			KEY_M:
				enquadrar_camera = not enquadrar_camera
				_atualizar_camera()
			KEY_R:
				carregar(caminho_mapa)
			KEY_TAB:
				var i := EXEMPLOS.find(caminho_mapa)
				carregar(EXEMPLOS[(i + 1) % EXEMPLOS.size()])
	elif evento is InputEventMouseButton and evento.pressed and not enquadrar_camera:
		if evento.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom_seguindo = minf(zoom_seguindo * 1.15, 8.0)
		elif evento.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom_seguindo = maxf(zoom_seguindo / 1.15, 0.5)
		camera.zoom = Vector2.ONE * zoom_seguindo


# ------------------------------------------------------------------ apoio

func _criar_marcador(tipo: int) -> Node2D:
	var m := Node2D.new()
	m.set_script(MarcadorScript)
	m.set("tipo", tipo)
	m.set("tamanho", tamanho_tile)
	add_child(m)
	return m


func _colocar(marcador: Node2D, celula: Vector2i) -> void:
	marcador.set("celula", celula)
	marcador.position = camada.map_to_local(celula)


func _posicionar_marcadores() -> void:
	var inicio := celula_inicio()
	_colocar(jogador, inicio)
	_colocar(escada, celula_mais_distante(inicio))


func _atualizar_camera() -> void:
	if dados.is_empty():
		return
	if enquadrar_camera:
		var tamanho_mapa := Vector2(int(dados["largura"]), int(dados["altura"])) * tamanho_tile
		var tela := get_viewport_rect().size
		# reserva a faixa da esquerda para o painel, para ele não cobrir o mapa
		var faixa := LARGURA_PAINEL if modo_interativo else 0.0
		var escala := minf((tela.x - faixa) / tamanho_mapa.x, tela.y / tamanho_mapa.y)
		camera.zoom = Vector2(escala, escala)
		camera.position = tamanho_mapa / 2.0 - Vector2(faixa / 2.0 / escala, 0)
	else:
		camera.position = jogador.position
		camera.zoom = Vector2.ONE * zoom_seguindo


func _atualizar_info() -> void:
	if _rotulo_info == null or dados.is_empty():
		return
	var linhas: Array = dados["linhas"]
	var piso := 0
	for l in linhas:
		piso += (l as String).count("1")
	var total := int(dados["largura"]) * int(dados["altura"])
	_rotulo_info.text = "Nível %d · %s · %d×%d · semente %s\nSalas: %d · Piso: %.0f%%" % [
		nivel, str(dados.get("algoritmo", "?")).to_upper(), int(dados["largura"]), int(dados["altura"]),
		str(int(dados.get("semente", 0))), (dados.get("salas", []) as Array).size(), 100.0 * piso / total]
	_status("")
	# o painel acompanha o mapa carregado
	var i_alg := ALGORITMOS.find(str(dados.get("algoritmo", "")))
	if i_alg >= 0:
		_opcao_algoritmo.selected = i_alg
	var i_tam := TAMANHOS.find(Vector2i(int(dados["largura"]), int(dados["altura"])))
	if i_tam >= 0:
		_opcao_tamanho.selected = i_tam
	_campo_semente.set_value_no_signal(int(dados.get("semente", 0)))


func _status(texto: String) -> void:
	if _rotulo_status != null:
		_rotulo_status.text = texto
		_rotulo_status.visible = not texto.is_empty()


func _criar_interface() -> void:
	var camada_ui := CanvasLayer.new()
	add_child(camada_ui)
	var painel := PanelContainer.new()
	painel.position = Vector2(12, 12)
	painel.custom_minimum_size.x = LARGURA_PAINEL - 24
	camada_ui.add_child(painel)
	var caixa := VBoxContainer.new()
	caixa.add_theme_constant_override("separation", 6)
	painel.add_child(caixa)

	var titulo := Label.new()
	titulo.text = "Gerador de masmorras"
	caixa.add_child(titulo)

	_opcao_algoritmo = OptionButton.new()
	for n in NOMES_ALGORITMOS:
		_opcao_algoritmo.add_item(n)
	caixa.add_child(_linha("Algoritmo", _opcao_algoritmo))

	_opcao_tamanho = OptionButton.new()
	for t in TAMANHOS:
		_opcao_tamanho.add_item("%d × %d" % [t.x, t.y])
	_opcao_tamanho.selected = 1
	caixa.add_child(_linha("Tamanho", _opcao_tamanho))

	_campo_semente = SpinBox.new()
	_campo_semente.max_value = 999999999
	_campo_semente.value = 7
	_campo_semente.value_changed.connect(func(_v): _campo_semente.get_line_edit().release_focus())
	var aleatoria := Button.new()
	aleatoria.text = "Aleatória"
	aleatoria.pressed.connect(func(): _campo_semente.value = randi() % 1000000)
	var linha_semente := _linha("Semente", _campo_semente)
	linha_semente.add_child(aleatoria)
	caixa.add_child(linha_semente)

	var botao := Button.new()
	botao.text = "Gerar masmorra"
	botao.pressed.connect(func(): nivel = 1; gerar_atual())
	caixa.add_child(botao)

	_rotulo_info = Label.new()
	caixa.add_child(_rotulo_info)
	_rotulo_status = Label.new()
	_rotulo_status.add_theme_color_override("font_color", Color("#ff8a80"))
	_rotulo_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_rotulo_status.custom_minimum_size.x = 280
	_rotulo_status.visible = false
	caixa.add_child(_rotulo_status)

	var ajuda := Label.new()
	ajuda.text = "Setas/WASD: andar · G: nova masmorra\nM: mapa inteiro/seguir · Roda: zoom\nChegue à escada laranja para o próximo nível"
	ajuda.add_theme_font_size_override("font_size", 12)
	caixa.add_child(ajuda)

	# botões e listas não roubam as setas do teclado
	for c in [_opcao_algoritmo, _opcao_tamanho, aleatoria, botao]:
		(c as Control).focus_mode = Control.FOCUS_NONE


func _linha(rotulo: String, controle: Control) -> HBoxContainer:
	var h := HBoxContainer.new()
	var l := Label.new()
	l.text = rotulo
	l.custom_minimum_size.x = 80
	h.add_child(l)
	controle.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(controle)
	return h


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
