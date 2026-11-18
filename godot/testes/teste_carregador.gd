extends SceneTree
## Testes automáticos da cena (rodam sem janela):
##   godot --headless --path <pasta godot> --script res://testes/teste_carregador.gd
## Sai com código 0 se tudo estiver certo e 1 caso contrário.

const MAPAS := ["res://mapas/exemplo_bsp.json", "res://mapas/exemplo_digger.json"]

var falhas := 0


func verificar(ok: bool, descricao: String) -> void:
	print("%s  %s" % ["OK   " if ok else "FALHA", descricao])
	if not ok:
		falhas += 1


func _initialize() -> void:
	# sem tipo estático: os métodos e campos usados vêm do script da cena
	var cena = load("res://cenas/masmorra.tscn").instantiate()
	cena.enquadrar_camera = false
	cena.modo_interativo = false
	root.add_child(cena)
	# o _ready() da cena só roda no primeiro quadro; espera antes de testar
	await process_frame

	# 1. desenho: tiles iguais ao JSON
	for caminho in MAPAS:
		if not cena.carregar(caminho):
			verificar(false, "%s: não carregou" % caminho)
			continue
		var esperado_piso := 0
		var esperado_parede := 0
		for linha in cena.dados["linhas"]:
			esperado_piso += linha.count("1")
			esperado_parede += linha.count("0")
		var camada: TileMapLayer = cena.get_node("TileMapLayer")
		var piso := camada.get_used_cells_by_id(0, Vector2i(1, 0)).size()
		var parede := camada.get_used_cells_by_id(0, Vector2i(0, 0)).size()
		verificar(piso == esperado_piso and parede == esperado_parede,
			"%s: piso %d/%d, parede %d/%d" % [caminho, piso, esperado_piso, parede, esperado_parede])

	# 2. jogador começa no piso e não atravessa paredes
	cena.carregar(MAPAS[0])
	var inicio: Vector2i = cena.jogador.celula
	verificar(cena.eh_piso(inicio), "jogador começa em célula de piso %s" % inicio)
	var andou := false
	for passo in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
		var antes: Vector2i = cena.jogador.celula
		var moveu: bool = cena.mover(passo)
		var depois: Vector2i = cena.jogador.celula
		if cena.eh_piso(antes + passo):
			andou = andou or (moveu and depois == antes + passo)
			cena.mover(-passo)
	verificar(andou, "jogador anda para células de piso")
	# empurra o jogador contra a parede: depois de muitos passos à esquerda ele para
	for i in 200:
		cena.mover(Vector2i.LEFT)
	var parado: Vector2i = cena.jogador.celula
	verificar(not cena.mover(Vector2i.LEFT) and cena.jogador.celula == parado and not cena.eh_piso(parado + Vector2i.LEFT),
		"jogador para ao encontrar parede em %s" % parado)

	# 3. escada fica no piso e é diferente do início
	var escada: Vector2i = cena.escada.celula
	verificar(cena.eh_piso(escada) and escada != cena.celula_inicio(), "escada em piso e longe do início %s" % escada)

	# 4. geração chamando o Python
	var gerou: bool = cena.gerar("digger", Vector2i(40, 30), 123)
	verificar(gerou and cena.dados.get("algoritmo") == "digger" and int(cena.dados["largura"]) == 40 and int(cena.dados["semente"]) == 123,
		"gera e carrega masmorra pelo Python (digger 40×30, semente 123)")

	quit(0 if falhas == 0 else 1)
