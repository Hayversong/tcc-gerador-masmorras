extends SceneTree
## Abre a cena com um mapa e salva uma captura da tela em PNG (precisa de janela,
## não funciona com --headless):
##   godot --path <pasta godot> --script res://ferramentas/capturar_tela.gd -- <mapa.json> <saida.png> [mapa|seguir|limpo]
## "mapa" (padrão): painel e mapa inteiro; "seguir": câmera no personagem;
## "limpo": só o mapa, sem painel nem personagem.
## <mapa.json> pode ser res://... ou um caminho absoluto; <saida.png> deve ser absoluto.


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var mapa: String = args[0] if args.size() > 0 else "res://mapas/exemplo_bsp.json"
	var saida: String = args[1] if args.size() > 1 else OS.get_user_data_dir().path_join("captura.png")

	var modo: String = args[2] if args.size() > 2 else "mapa"
	var cena = load("res://cenas/masmorra.tscn").instantiate()
	cena.caminho_mapa = mapa
	cena.modo_interativo = modo != "limpo"
	cena.enquadrar_camera = modo != "seguir"
	root.add_child(cena)
	for i in 5:
		await process_frame
	await RenderingServer.frame_post_draw

	var erro := root.get_texture().get_image().save_png(saida)
	print("captura salva em %s (erro=%d)" % [saida, erro])
	quit(0 if erro == OK else 1)
