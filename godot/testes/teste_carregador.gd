extends SceneTree
## Teste automático do carregador (roda sem janela):
##   godot --headless --path godot --script res://testes/teste_carregador.gd
## Para cada mapa de exemplo, confere se o número de tiles de piso e de parede
## desenhados é igual ao número de "1" e "0" no JSON. Sai com código 0 se
## tudo estiver certo e 1 caso contrário.

const MAPAS := ["res://mapas/exemplo_bsp.json", "res://mapas/exemplo_digger.json"]


func _initialize() -> void:
	# sem tipo estático: os métodos e campos usados vêm do script da cena
	var cena = load("res://cenas/masmorra.tscn").instantiate()
	cena.enquadrar_camera = false
	root.add_child(cena)
	# o _ready() da cena só roda no primeiro quadro; espera antes de testar
	await process_frame

	var falhas := 0
	for caminho in MAPAS:
		if not cena.carregar(caminho):
			print("FALHA  %s: não carregou" % caminho)
			falhas += 1
			continue
		var esperado_piso := 0
		var esperado_parede := 0
		for linha in cena.dados["linhas"]:
			esperado_piso += linha.count("1")
			esperado_parede += linha.count("0")
		var camada: TileMapLayer = cena.get_node("TileMapLayer")
		var piso := camada.get_used_cells_by_id(0, Vector2i(1, 0)).size()
		var parede := camada.get_used_cells_by_id(0, Vector2i(0, 0)).size()
		var ok := piso == esperado_piso and parede == esperado_parede
		print("%s  %s: piso %d/%d, parede %d/%d" % ["OK   " if ok else "FALHA", caminho, piso, esperado_piso, parede, esperado_parede])
		if not ok:
			falhas += 1

	quit(0 if falhas == 0 else 1)
