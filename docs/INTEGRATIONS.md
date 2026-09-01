# Integrações

O `audioguard` é agnóstico de quem gera os arquivos de config em `CHANNELS_DIR` — ele só lê `*.yaml`/`*.yml` desse diretório (ver `cli.py::cmd_run_dir`). Isso permite integrações externas escreverem configs automaticamente sem o `audioguard` precisar saber nada sobre elas.

## Exemplo: bridge com um orquestrador de canais existente

Um padrão comum: um sistema já orquestra canais de streaming e sabe, por canal, se existe uma faixa de áudio real na origem (ex.: por bitrate configurado por pipe). Nesse caso, faz sentido rodar `audioguard` **só** para os canais que têm vídeo mas não têm áudio — os demais continuam servidos pelo pipeline existente, sem passar pelo `audioguard`.

Um script externo (fora deste repo) pode implementar esse contrato:

1. Consultar periodicamente o sistema de origem pra descobrir quais canais têm vídeo sem áudio.
2. Para cada um, escrever um `<CHANNELS_DIR>/<id>.yaml` no formato de [`examples/channel.yaml`](../examples/channel.yaml).
3. Remover arquivos que ele mesmo gerou para canais que deixaram de se qualificar (ganharam áudio real, ou saíram do ar).
4. Se o conjunto de arquivos mudou, reiniciar a unit systemd do `audioguard` (`run-dir` lê o diretório uma vez na subida — não há hot-reload ainda, ver "Limitações" abaixo).

**Convenção de nomeação:** se você seguir esse padrão, nomeie a unit systemd do `audioguard` como `audioguard.service` — é o nome que um script de bridge típico vai assumir ao chamar `systemctl restart`.

**Isolamento seguro:** um bridge externo nunca deve apagar um `.yaml` que não foi ele quem criou. Prática recomendada: marcar os arquivos gerados com uma linha de comentário fixa no topo (ex.: `# gerado por <nome-do-bridge> - nao editar a mao`) e, ao decidir o que remover, só considerar arquivos com essa marca.

## Limitações atuais

- **Sem hot-reload.** `run-dir` lê `CHANNELS_DIR` uma única vez, na subida do processo. Uma integração externa que adiciona/remove canais precisa reiniciar o `audioguard` pra aplicar a mudança (ver `supervisor.py`/`cli.py` — nenhum deles observa o diretório continuamente ainda).
- **Nenhuma API externa própria.** `audioguard` não expõe HTTP/RPC pra outros sistemas consultarem estado — integrações são unidirecionais (escrevem config, o `audioguard` só lê).

Essas duas limitações são candidatas naturais pra v0.2 se o padrão de integração externa se confirmar necessário (watch no diretório + reload gracioso, em vez de restart completo do processo).
