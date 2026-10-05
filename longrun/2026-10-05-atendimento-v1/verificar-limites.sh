#!/usr/bin/env bash
# Camada "limite" do goal.md. Imprime LIMITES OK ou o primeiro problema (código ≠ 0).
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
D=longrun/2026-10-05-atendimento-v1
falha() { echo "LIMITE VIOLADO: $*"; exit 1; }
[ -f $D/hash-congelado.txt ] || falha "contrato não congelado (rode $D/congelar.sh)"
source $D/hash-congelado.txt
h=$(cat $(git ls-files tests pytest.ini docs/ESPECIFICACAO.md $D/verificar-limites.sh | sort) | sha256sum | cut -c1-16)
[ "$h" = "$HASH" ] || falha "hash do contrato mudou ($h ≠ $HASH)"
git diff --quiet -- tests pytest.ini docs/ESPECIFICACAO.md || falha "contrato alterado no working tree"
n=$(python3 -m pytest --collect-only -q 2>/dev/null | grep -oE '^[0-9]+ tests? collected' | grep -oE '^[0-9]+')
[ "$n" = "$TESTES" ] || falha "nº de testes coletados $n ≠ $TESTES"
fora=$( { git diff --name-only "$BASE"; git ls-files --others --exclude-standard; } | sort -u \
  | grep -vE "^($D/|atende$|src/|web/|exemplos/|README\.md$|VERSION$|\.gitignore$|CLAUDE\.md$|FALHAS\.md$)" )
[ -z "$fora" ] || falha "arquivos fora do escopo: $(echo $fora)"
alvo=$(ls -d atende src web 2>/dev/null)
[ -n "$alvo" ] || falha "não há implementação (atende/src/web)"
grep -rnE '^\s*(import|from)\s+(requests|httpx|aiohttp|urllib3|flask|fastapi|django|openai|anthropic|groq)\b' $alvo && falha "dependência externa ou SDK de API"
grep -rniE 'OPENAI|ANTHROPIC|GROQ|OPENROUTER|graph\.facebook|whatsapp\.com|api_key|apikey' $alvo && falha "referência a API/chave"
grep -rnP 'https?://(?!127\.0\.0\.1|localhost|www\.w3\.org)' $alvo && falha "URL externa no código"
grep -rn '0\.0\.0\.0' $alvo && falha "bind em 0.0.0.0"
echo "LIMITES OK (hash $HASH, $TESTES testes, escopo ok, sem API/rede)"
