extends Node2D
## Marcador desenhado em código sobre uma célula da grade: o jogador ou a
## escada para o próximo nível. Não depende de arte.

enum Tipo { JOGADOR, ESCADA }

@export var tipo: Tipo = Tipo.JOGADOR
@export var tamanho: int = 16

## Célula da grade em que o marcador está.
var celula: Vector2i = Vector2i.ZERO


func _draw() -> void:
	var t := float(tamanho)
	if tipo == Tipo.JOGADOR:
		draw_circle(Vector2.ZERO, t * 0.38, Color("#2a78d6"))
		draw_circle(Vector2.ZERO, t * 0.38, Color.WHITE, false, maxf(1.0, t / 16.0))
	else:
		var r := Rect2(-t * 0.42, -t * 0.42, t * 0.84, t * 0.84)
		draw_rect(r, Color("#eb6834"))
		# três degraus
		for i in 3:
			var y := r.position.y + r.size.y * (0.3 + 0.25 * i)
			draw_line(Vector2(r.position.x + 2, y), Vector2(r.end.x - 2, y), Color.WHITE, maxf(1.0, t / 16.0))
