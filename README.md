# Vila em Tempo Real — Taverna

## Integrantes
- Luana Aparecida Guilherme — @luana-codes

## Como instalar e executar
Pré-requisitos: Python 3 e Git.

```
git clone https://github.com/luana-codes/lpp-trabalho01-luana-guilherme.git
cd lpp-trabalho01-luana-guilherme
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux ou macOS
pip install -r requirements.txt
uvicorn server:app --reload
```

Abra `http://localhost:8000` no navegador (não abra o arquivo direto, com `file://`). Se a porta 8000 estiver ocupada, use `uvicorn server:app --reload --port 8001` e abra `http://localhost:8001`.

## Como testar com duas abas
1. Abra http://localhost:8000 em duas abas, lado a lado.
2. Na primeira, digite um nome e clique em Entrar como Mestre. Na segunda, digite outro nome e clique em Entrar como Jogador.
3. Nas duas abas devem aparecer Ingredientes 150, Cozinheiros 0/2 e a faixa "Aguardando o Mestre".
4. Recusa: no Jogador, clique em Preparar prato antes de abrir. Só essa aba recebe o aviso "A taverna não está aberta".
5. Abertura: no Mestre, clique em Abrir taverna. Nas duas abas, a faixa muda para "Taverna aberta", e os ingredientes passam a subir de 10 em 10 a cada 5 segundos.
6. Preparo: no Jogador, clique em Preparar prato. Os ingredientes caem 50, os cozinheiros ocupados vão para 1/2 e um fogão com barra de progresso aparece nas duas abas.
7. Fim do preparo: o tempo é sorteado entre 5 e 12 segundos. Até 10 segundos, o prato fica pronto (pratos prontos +1, produção +5). Com 11 ou 12 segundos, o cliente desiste (cliente.desistiu), sem prato. Repita até ver os dois resultados.
8. Limite: com os 2 cozinheiros ocupados, um novo pedido é recusado com "Sem cozinheiro livre".
9. Disputa: abra uma terceira aba de Jogador. Com 1 cozinheiro ocupado, clique em Preparar prato nas duas abas de Jogador quase ao mesmo tempo. Só uma consegue, e a outra recebe "Sem cozinheiro livre".
10. Encerramento: no Mestre, clique em Encerrar taverna. A tela escurece, os ingredientes param de subir e qualquer pedido novo é recusado.
11. Em cada aba, o Painel de eventos mostra cada evento emitido (⬆ emit) e escutado (⬇ on), com horário, dados, causa e reação.

## Perguntas
1. Quais eventos o seu sistema emite e escuta?

**O cliente emite três pedidos:** taverna.abertura_solicitada e taverna.encerramento_solicitado (o Mestre) e prato.solicitado (o Jogador).

**O servidor escuta** esses três pedidos e decide o que fazer com cada um.

**O servidor emite os fatos:** estado.sincronizado, taverna.iniciada, preparo.iniciado, operacao.recusada, ingrediente.produzido, prato.concluido, cliente.desistiu e taverna.encerrada.

**O cliente escuta** todos esses fatos e reage a cada um (atualiza a tela, mostra um aviso e anima a taverna). Os pedidos do cliente ficam separados dos fatos do servidor, e a recusa também é um evento, enviado só para quem pediu.

2. Como o sistema sabe quando deve atualizar os outros jogadores?

Ele não precisa verificar nada. Cada vez que o servidor muda o estado, ele emite um evento para todos os clientes conectados, e cada cliente tem um ouvir(...) registrado para aquele evento. O cliente nunca pergunta "mudou alguma coisa?" e nunca altera o estado sozinho: o estado só muda quando chega um evento do servidor.

Quando o gatilho não é uma ação de alguém, ele vem de um temporizador do servidor. É o caso de ingrediente.produzido (a cada 5 segundos) e de prato.concluido ou cliente.desistiu (quando o preparo termina). O painel de eventos mostra a causa de cada fato, seja um pedido ou o temporizador.

3. Que parte do código mostra claramente o uso do paradigma orientado a eventos?

- `server.py`, função `producao()`: um temporizador que emite `ingrediente.produzido` para todos, sem ninguém clicar.
- `server.py`, função `preparo()`: ao fim do tempo sorteado, o servidor emite um entre `prato.concluido` e `cliente.desistiu`.
- `server.py`, função `preparar_prato()`: escuta `prato.solicitado`, valida tudo sem `await` no meio e emite `preparo.iniciado` (para todos) ou `operacao.recusada` (só para quem pediu). É isso que resolve a disputa entre dois jogadores.
- `client/index.html`, bloco "ESCUTAS" dentro de `entrar()`: cada `ouvir(evento, reação, função)` liga um evento do servidor a uma reação na tela.
- `client/index.html`, funções `ouvir(...)` e `pedir(...)`: envolvem `socket.on` e `socket.emit` e registram cada evento no Painel de eventos.

## Uso de IA

Usei o Claude (Anthropic) como apoio durante o trabalho: para revisar a especificação, seguir o passo a passo do Guia de Implementação, adaptar o código do kit para o tema da taverna (renomear eventos, estado e textos), conferir os arquivos e planejar os testes.

Sobre o evento `cliente.desistiu`: a regra já constava na minha especificação. O Claude apontou que, como estava escrita (cozimento de 8s e paciência de 15s), ela nunca dispararia, e sugeriu o tempo de preparo sorteado entre 5 e 12s com paciência de 10s. Implementei e testei essa versão.

O que eu fiz e mudei: escrevi a especificação e escolhi as regras da taverna, digitei e salvei o código em cada etapa, testei cada etapa com duas ou mais abas, ajustei textos, emojis e comentários e fiz os commits.

## Extras
- Evento próprio da taverna, cliente.desistiu, com o tempo de preparo sorteado entre 5 e 12 segundos e a paciência do cliente de 10 segundos.

- Cada preparo recebe um id, para a tela remover o fogão certo quando termina.
