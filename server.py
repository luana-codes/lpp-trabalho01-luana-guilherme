import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

CUSTO = 50
TEMPO_OBRA = 8
INTERVALO = 5

estado = {
    "fase": "aguardando",
    "toras": 150,
    "trabalhadores": 0,
    "limite": 2,
    "producao": 10,
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO,
    "concluidas": 0,
    "em_obra": 0,
}

jogadores = {}

def fato(causa, **extras):
    return {"estado": dict(estado), "causa": causa, **extras}

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
