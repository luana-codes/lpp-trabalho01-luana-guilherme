import random
import socketio
 
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da taverna
})
 
CUSTO = 50           # ingredientes por prato
INTERVALO = 5        # segundos entre as produções
PACIENCIA = 10       # segundos que o cliente espera pelo prato
TEMPO_MIN = 5        # menor tempo de preparo (sorteado)
TEMPO_MAX = 12       # maior tempo de preparo (sorteado)
 
# O servidor é a fonte da verdade: só ele altera este estado.
estado = {
    "fase": "aguardando",      # aguardando -> aberta -> encerrada
    "ingredientes": 150,
    "cozinheiros": 0,          # ocupados agora
    "limite": 2,
    "producao": 10,            # ingredientes produzidos a cada INTERVALO
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_MAX,   # tempo do último preparo (a barra da tela usa)
    "custo": CUSTO,
    "pratos": 0,               # pratos prontos
    "em_preparo": 0,
}
 
jogadores = {}     # sid -> {"nome": ..., "papel": ...}
proximo_id = 0     # identifica cada preparo, para a tela saber qual terminou
 
 
def fato(causa, **extras):
    """Payload de um FATO: estado atual + a CAUSA que o gerou."""
    return {"estado": dict(estado), "causa": causa, **extras}
 
 
async def recusar(sid, motivo, causa):
    """A recusa também é um evento, mas vai só para quem pediu."""
    await sio.emit("operacao.recusada", {"motivo": motivo, "causa": causa}, to=sid)
 
 
@sio.event
async def connect(sid, environ, auth):
    auth = auth or {}
    jogadores[sid] = {
        "nome": auth.get("nome", "Anônimo"),
        "papel": auth.get("papel", "jogador"),
    }
    # servidor -> UM cliente: só o recém-chegado precisa do estado
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)
 
 
@sio.event
async def disconnect(sid):
    jogadores.pop(sid, None)
 
# escuta o PEDIDO do Mestre: só o servidor decide se a taverna pode abrir
@sio.on("taverna.abertura_solicitada")
async def abrir_taverna(sid, dados=None):
    pedido = "taverna.abertura_solicitada"
    if jogadores[sid]["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode abrir a taverna", pedido)
        return
    if estado["fase"] != "aguardando":
        await recusar(sid, "A taverna já foi aberta", pedido)
        return
    estado["fase"] = "aberta"
    sio.start_background_task(producao)   # o temporizador passa a gerar eventos
    # servidor -> TODOS: a taverna abriu
    await sio.emit("taverna.iniciada", fato(pedido))
 
# escuta o PEDIDO do Jogador: o servidor valida e só então emite o fato
@sio.on("prato.solicitado")
async def preparar_prato(sid, dados=None):
    global proximo_id
    pedido = "prato.solicitado"
 
    # Valida TUDO e altera o estado sem await no meio:
    # pedidos simultâneos são decididos um de cada vez.
    if estado["fase"] != "aberta":
        motivo = "A taverna não está aberta"
    elif estado["ingredientes"] < CUSTO:
        motivo = "Ingredientes insuficientes"
    elif estado["cozinheiros"] >= estado["limite"]:
        motivo = "Sem cozinheiro livre"
    else:
        motivo = None
 
    if motivo:
        await recusar(sid, motivo, pedido)   # só quem pediu recebe
        return
 
    tempo = random.randint(TEMPO_MIN, TEMPO_MAX)
    proximo_id += 1
    pid = proximo_id
    estado["ingredientes"] -= CUSTO
    estado["cozinheiros"] += 1
    estado["em_preparo"] += 1
    estado["tempo_obra"] = tempo
    nome = jogadores[sid]["nome"]
    # servidor -> TODOS: o pedido foi aceito e o preparo começou
    await sio.emit("preparo.iniciado", fato(pedido, por=nome, tempo=tempo, id=pid))
    sio.start_background_task(preparo, nome, tempo, pid)
 
 
async def producao():
    # temporizador do servidor: fonte de eventos, ninguém clica
    while estado["fase"] == "aberta":
        await sio.sleep(INTERVALO)
        if estado["fase"] != "aberta":
            break
        estado["ingredientes"] += estado["producao"]
        # servidor -> TODOS: o fato nasce do temporizador, não de um pedido.
        # Todos precisam ver o estoque subir ao mesmo tempo, e por isso o
        # cliente nunca pergunta "já produziu?": ele só escuta este evento.
        await sio.emit("ingrediente.produzido", fato("temporizador"))
 
 
async def preparo(nome, tempo, pid):
    # temporizador do preparo: ao final, emite UM entre prato.concluido e cliente.desistiu
    await sio.sleep(tempo)
    if estado["fase"] != "aberta":
        return
    estado["cozinheiros"] -= 1
    estado["em_preparo"] -= 1
    causa = "preparo.iniciado (temporizador)"
    if tempo > PACIENCIA:
        # servidor -> TODOS: o temporizador do preparo estourou a paciência do
        # cliente. Este fato substitui prato.concluido (nunca saem os dois).
        await sio.emit("cliente.desistiu", fato(causa, por=nome, id=pid))
    else:
        estado["pratos"] += 1
        estado["producao"] += 5   # cada prato pronto aumenta a produção
        # servidor -> TODOS: o preparo terminou dentro da paciência do cliente
        await sio.emit("prato.concluido", fato(causa, por=nome, id=pid))
 
# escuta o PEDIDO do Mestre: o servidor encerra e passa a recusar novas ações
@sio.on("taverna.encerramento_solicitado")
async def encerrar_taverna(sid, dados=None):
    pedido = "taverna.encerramento_solicitado"
    if jogadores[sid]["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode encerrar a taverna", pedido)
        return
    if estado["fase"] != "aberta":
        await recusar(sid, "A taverna não está aberta", pedido)
        return
    estado["fase"] = "encerrada"
    # servidor -> TODOS: novas ações passam a ser recusadas
    await sio.emit("taverna.encerrada", fato(pedido))