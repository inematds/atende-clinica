# FALHAS

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-10-05 | leitura usou nomes de arquivos inexistentes e repetiu tail abreviado | conferir caminhos com rg --files e usar tail -n | prompt |
| 2026-10-05 | tail com opção antiga e múltiplos arquivos recusou leitura | usar `tail -n 20` | prompt |
