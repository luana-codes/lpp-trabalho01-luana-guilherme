# Especificação — Taverna em Tempo Real

**Integrante(s):** Luana Aparecida Guilherme (@luana-codes)

**Repositório:** https://github.com/luana-codes/lpp-trabalho01-luana-guilherme

**Tipo de vila (sorteio):** Taverna

## 1. Regras da vila

- **Recursos:** Ingredientes (primário) e Pratos Prontos (refinado).
- **Estoque inicial:** 150 ingredientes e 0 pratos prontos.
- **Custo de um preparo:** 50 ingredientes por prato.
- **Tempo do preparo:** sorteado entre 5 e 12 segundos.
- **Paciência do cliente:** 10 segundos. Se o preparo passar disso, o cliente desiste.
- **Limite de cozinheiros:** 2 trabalhando ao mesmo tempo.
- **Produção automática:** 10 ingredientes a cada 5 segundos, com a taverna aberta.
- **Quando um prato é concluído:** o cozinheiro fica livre, os pratos prontos aumentam em 1 e a produção aumenta em +5 por ciclo.
- **Quando o cliente desiste:** o cozinheiro fica livre, os ingredientes não são devolvidos e nenhum prato é contabilizado.
- **Motivos de recusa:** taverna não está aberta; ingredientes insuficientes; sem cozinheiro livre; só o Mestre pode abrir ou encerrar.

## 2. Eventos

| Evento | Emite | Recebe | O que muda no estado |
|---|---|---|---|
| `taverna.abertura_solicitada` | Mestre | Servidor | Pedido; nada muda. |
| `taverna.iniciada` | Servidor | Todos | Fase vira "aberta"; a produção de ingredientes começa. |
| `prato.solicitado` | Jogador | Servidor | Pedido; nada muda. |
| `preparo.iniciado` | Servidor | Todos | Debita 50 ingredientes, ocupa 1 cozinheiro, soma 1 em preparo. |
| `operacao.recusada` | Servidor | Só quem pediu | Nada muda; envia o motivo. |
| `ingrediente.produzido` | Servidor | Todos | Ingredientes +produção do ciclo. |
| `prato.concluido` | Servidor | Todos | Libera 1 cozinheiro, pratos prontos +1, produção +5. |
| `cliente.desistiu` | Servidor | Todos | Libera 1 cozinheiro; sem ganho de prato. |
| `taverna.encerramento_solicitado` | Mestre | Servidor | Pedido; nada muda. |
| `taverna.encerrada` | Servidor | Todos | Fase vira "encerrada"; temporizadores param; novos pedidos são recusados. |

## 3. Cenários de teste (Dado / Quando / Então, escritos com eventos)

### Recusa
Dado que há 2 de 2 cozinheiros ocupados, quando o Jogador A emite `prato.solicitado`, então o servidor emite `operacao.recusada` (motivo: "Sem cozinheiro livre") apenas para o Jogador A, e nenhum outro jogador recebe nada.

### Passagem do tempo
Dado que a taverna está aberta e um prato está em preparo, quando passam 5 segundos, então o servidor emite `ingrediente.produzido` para todos (+10 ingredientes). Quando o tempo de preparo termina dentro da paciência do cliente, então o servidor emite `prato.concluido` para todos, liberando 1 cozinheiro.

### Disputa entre dois jogadores
Dado que há 1 de 2 cozinheiros ocupados e ingredientes suficientes, quando os jogadores A e B emitem `prato.solicitado` ao mesmo tempo, então o servidor processa um por vez: emite `preparo.iniciado` para todos (resultado do pedido de A) e `operacao.recusada` ("Sem cozinheiro livre") apenas para B.
